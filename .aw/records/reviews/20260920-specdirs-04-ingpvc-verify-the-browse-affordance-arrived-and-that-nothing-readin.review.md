# Review: verify the browse affordance arrived and that nothing reading a spec broke, child ingpvc (Set specdirs)

- Subject-Id: ingpvc
- Subject-Type: ipd
- Reviewed-At: 2026-09-21
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed in an isolated lane worktree at HEAD `65a14010`. `aw ipd lint --phase author` CONFORMING
before semantic review, and `--phase review-finalize` CONFORMING after every revision, with zero
findings at both checkpoints.

THIS IS A SELF-REVIEW IN THE AUTHORSHIP SENSE AND THAT IS STATED UP FRONT: the plan's `- Author:` is
the same agent/model string as this reviewer. Nothing below therefore rests on the plan's own prose.
Every load-bearing claim was re-derived by RUNNING the shipped predicates or reading the cited symbol
at HEAD, and all five findings this review adds were found that way, including two that correct the
plan's own numbers and citations.

THE PLAN'S PREMISE IS CORRECT AND ITS SHAPE IS THE PRESCRIBED ONE. `ROLLUP_OMITTED_GATES` really does
carry exactly one omission, `pre-transition-ev-checkpoint`, with the recorded reason that "an
orchestrator's items are performed by NOBODY (the runner supersedes its coordination role)". So a
runner retiring `wfjsp4` really would mark E-01..E-04 complete unperformed and unverified, and a child
that OWNS that work under a real E/V checkpoint is the right answer. The plan's approach also matches
`runner_shared.probe_refusal_remedy` verbatim ("author a child plan ... add its row to the
orchestrator's `## Child IPDs` table, and leave the parent's existing checklist in place. Do NOT
delete the parent's items"), which is the strongest possible evidence that the shape is right rather
than merely plausible. Its row IS present in the parent's table at `:85`.

THE DETERMINISTIC RETIREMENT GATE WAS RUN RATHER THAN REASONED ABOUT, and it confirms the plan's claim
that authoring `r9uvwc` cleared the `unauthored-child-rows` refusal:
`runner_shared.evaluate_set_retirement(repo, 'specdirs')` returns `eligible=False` with reason
`unfinished-children` and detail `y4bdoz (approved), 1bdxcp (approved), r9uvwc (reviewed), ingpvc
(to-review)`. Since the reason is the child-status one and not the row one, every declared row now
resolves to a plan on disk.

THE MOST CONSEQUENTIAL FINDING IS THAT THE PLAN OVERSTATED WHAT IT ACHIEVES, and it is the one a
reader would most likely have believed (PR-001). The plan said adding its row to the parent's table
"lets the coverage gate pass". It does not follow, and the code says why. The gate is a MODEL
JUDGEMENT, not an existence check for a covering child: `orchestrator_probe_excerpt` sends the
parent's own checklist ACTION TEXT plus its child-table ROW CELLS and no child's contents, and
`PROBE_PROMPT_TEMPLATE` enumerates "an item that reconciles records, runs a repo-wide suite, performs
a whole-Set verification or audit" as work no child covers, then adds "any doubt resolves to
CONTAINS EXECUTIONS" because under-reporting is the expensive direction. I rendered the actual excerpt
for `wfjsp4`: 9934 characters, still containing `VERIFY THE BROWSE AFFORDANCE`, `VERIFY NOTHING THAT
READS`, `VERIFY THE INVARIANT SURVIVES` and `RUN THE SUITE BARE`, with `ingpvc` appearing only as a
row cell. So a model can legitimately answer CONTAINS EXECUTIONS after this plan exists. This matters
in two directions and both are now written into the plan: an executor must not report the gate as
broken when it refuses again, and nobody must "fix" it by deleting the parent's items, which is the
exact compliance-by-deletion failure `probe_refusal_remedy` was worded to prevent. The honest remedy
is `--allow-uncovered-orchestrator-work '<why>'`, which requires a justification and records it. The
real value of this plan is unchanged by any of that: it makes the parent's items PERFORMED AND
EVIDENCED under a checkpoint, which is the defect that actually costs something.

A GENUINE EXECUTABILITY IMPOSSIBILITY (PR-002). E-02 required pasting BEFORE and AFTER
`ls .aw/records/specs/` listings side by side, but the plan declares
`Item-Dependencies: ... executed:1bdxcp`, so by construction it runs only after the migration has
already moved every spec. There is no moment at which it can observe the pre-migration tree. Left
unrepaired, an executor either skips the Set's primary acceptance evidence or fabricates it, and
fabricating it is the more likely outcome because the item reads as mandatory. The repair is exact
rather than a weakening: reconstruct the BEFORE half from git, verified viable at review
(`git ls-tree --name-only HEAD~1 .aw/records/specs/` renders the flat list), and require it be
LABELLED git-reconstructed with its commit named so no reader mistakes it for a live measurement.

TWO OF THE PLAN'S OWN NUMBERS AND TWO OF ITS OWN CITATIONS DID NOT SURVIVE RE-MEASUREMENT, which is
notable because this plan's whole argument is that a re-measuring child beats a parent asserting
12-day-old figures. Its citation audit (51 distinct / 33 resolve / 18 dangling) did not reproduce in
any form; three defensible enumerations of the same tree at the same commit gave 68/28/40 (every
distinct literal), 54/28/26 (dropping 14 `...`-elided prose forms that can never resolve) and
44/28/16 (also excluding `tests/`). The lesson is not that the plan was careless but that the metric
is dominated by METHOD, so a number without its method makes the before/after comparison meaningless
even when both halves are honest; V-03 now requires the method be stated first. Its "only TWO real
danglers" claim is also too strong: both named ones reproduce exactly
(`agy_run.py:122` -> `20260809-2211-01-aw-project-layout.spec.md`, and `u06zo2` ->
`20260920-llbr2b-...` at four lines), but the non-fixture dangling set also includes illustrative
citations inside executed plans and review records, plus probe artifacts cited by this Set's OWN
pending plans, and counting those as damage would misattribute plan prose to the migration.
Separately, its E-04 citation of the dual-spelling bypass comments (`status_set.py:517-525`,
`:549-556`) is stale: that range now holds row-rendering and color code, and the real comments are at
`:611-617` and `:643-649` with mirrors at `specs.py:599-601` and `:613-615`.

WHAT I CHECKED AND FOUND SOUND, recorded so an absent finding is not read as an absent review. The
`aw specs check --json` claim is exactly right and I confirmed `{"checked": 36, "violations": 0}` on
the live tree, along with the retired-filter triple (`_spec_files` 36, `_iter_type_files` default 19,
`include_retired=True` 36, sets equal by name) and the 36-file distribution 15 `implemented` /
13 `approved` / 2 each `superseded`,`draft`,`deferred` / 1 each `to-review`,`implementing`. Both
`Carrier-Declined` carriers resolve and are live (`uwerb5` open, `ajomj3` open, the latter filed
specifically for the two danglers). The per-RULE-ID rather than repo-wide check comparison is correct
and materially important: a bare `aw check` here reports hundreds of pre-existing findings. The
suite-baseline instruction (measure your own, judge the failing node-id delta, do not delete another
party's untracked directory) is correct. V-04's requirement that the executor STATE WHO PERFORMED THE
ITEM AND IN WHAT MODE is unusually good for a plan whose whole reason for existing is that the
previous answer was "nobody". The `Readiness` absence was correct at `to-review` and I did not treat
it as an omission.

THE SUITE WAS NOT RUN IN THIS REVIEW, deliberately and disclosed: this review changed no code, only a
planning document and a review record, so there is no code result to report. The plan's own V-03
mandates the node-id delta at execution.

`aw check` WAS RUN BEFORE AND AFTER these edits and the delta is EMPTY: 365 findings on both sides,
with no rule/location pair added and none removed, so this review introduces no new drift. (The 365
baseline already includes the one `check.ipd-dependency-findings-blocked` row on THIS plan that the
sibling review of `r9uvwc` correctly created, because this plan declares `executed:r9uvwc` and that
plan now carries an unresolved gating finding. That row is expected and clears when `r9uvwc`'s OQ-03
is answered; it is not a defect in this plan.) `aw sanitize --agent` clean, and neither file contains
an em or en dash.

SCOPE: only this plan was a candidate. Read as evidence: `agent_workflows/runner_shared.py`
(`allocate_isolation_worktree` `:1024`, `evaluate_set_retirement` `:8332`, `PROBE_VERDICT_UNKNOWN`
`:8494`, `record_probe_verdict` `:8718`, `PROBE_SENTINEL_*` `:8903-8904`, `PROBE_REFUSAL_CODE` `:8920`,
`PROBE_PROMPT_TEMPLATE` `:8951-8985`, `render_probe_prompt` `:8987`, `orchestrator_probe_excerpt`
`:9002`, `probe_refusal_remedy` `:9415-9439`), `agent_workflows/ipd_lifecycle.py`
(`_is_implicitly_allowed` `:1810-1827`, `_working_tree_path_is_owned` `:1830`, the scope audit
`:2100-2125`, the ack computation `:2528-2560`, `ROLLUP_OMITTED_GATES` `:2989`, `retire_orchestrator`
`:3107-3160`), `agent_workflows/oc_runipd.py` (`dependency_depth` `:4246`, `queue_sort_key` `:4281`,
`simulate_dispatch_order` `:4330`, the isolation/integrate-back contract `:2215-2231`, the audit-lane
isolation `:7882-7905`), `agent_workflows/status_set.py` (`:517-560` rendering, the two bypass
comments `:611-617` and `:643-649`), `agent_workflows/specs.py:599-615`,
`agent_workflows/ipd_schema.scope_paths_implicit_allowances`, plans `wfjsp4` (`:85`, `:87`, `:89`,
`:91`), `y4bdoz`, `1bdxcp`, `r9uvwc`, backlog `uwerb5`, `ajomj3`, the live `.aw/records/specs/` tree,
and a `git grep` citation enumeration over tracked text.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / F. Honest docs | `agent_workflows/runner_shared.py:8951-8985,9002,9415-9439` | THE PLAN CLAIMED ADDING ITS ROW "lets the coverage gate pass". It does not follow. The gate is a MODEL judgement over the parent's OWN checklist action text plus child-table row cells, with no child contents; the rendered `wfjsp4` excerpt is 9934 chars and still contains all four `VERIFY`/`RUN THE SUITE` items, while the prompt names "performs a whole-Set verification or audit" as work-no-child-covers and says "any doubt resolves to CONTAINS EXECUTIONS". A refusal therefore remains legitimate after this plan exists, and a reader believing otherwise would either report the gate broken or delete the parent's items to satisfy it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate section rewritten with both mechanisms measured, the correct reading stated (this plan's value is that the items become performed AND verified, independent of the probe verdict), the `--allow-uncovered-orchestrator-work` remedy named, and an explicit prohibition on deleting the parent's items. Added as F-10 and as a conventions bullet. |
| PR-002 | HIGH | UNDER-SCOPE | E. Testing / G. Executability | plan `- Item-Dependencies:` line 8 vs E-02 | E-02 REQUIRED AN UNOBSERVABLE MEASUREMENT: it demands a BEFORE `ls .aw/records/specs/`, but the plan declares `executed:1bdxcp`, so it runs only after the migration moved every spec and can never observe the pre-migration tree. The Set's PRIMARY acceptance evidence was therefore either unobtainable or an invitation to fabricate. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now requires the BEFORE half be reconstructed with `git ls-tree --name-only <sha> .aw/records/specs/` (verified viable at review), LABELLED git-reconstructed, and its commit named; V-02 refuses a BEFORE listing presented as a live `ls`. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `git grep` enumeration; `u06zo2`; `agy_run.py:122` | THE CITATION FIGURES DO NOT REPRODUCE AND THE DANGLER CLAIM IS TOO STRONG. Three defensible enumerations of the same tree at the same commit gave 68/28/40, 54/28/26 and 44/28/16; none equals the authored 51/33/18. The two named danglers do reproduce, but the non-fixture dangling set also includes illustrative citations in executed plans and review records plus probe artifacts cited by this Set's own pending plans, so "only TWO real ones" would misattribute plan prose to the migration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now leads with the DELTA rule (which was always the load-bearing instruction), records all three re-measured triples, requires the enumeration METHOD be stated before any number, and requires the pre-existing set be classified rather than asserted as two. V-03 refuses a bare triple with no method. Added as F-11 plus a conventions bullet. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness | `status_set.py:611-617,643-649`; `specs.py:599-615` | TWO OF THE PLAN'S OWN CITATIONS ARE STALE while its F-09 warns that line numbers move: `status_set.py:517-525` and `:549-556` now hold row-rendering and color code, not the dual-spelling bypass comments. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 corrected with the current locations and the mirrored pair in `specs.py`, plus an instruction to verify by symbol or by grepping the comment text rather than re-quoting a line number. Added as F-12. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Executability | plan `## Approval and execution gate`; `ipd_schema.scope_paths_implicit_allowances`; `ipd_lifecycle.py:2528-2560` | THE GATE WAS MISSING THREE REQUIRED CONTRACT ELEMENTS (no scope fence, no explicit paste-the-actual-output honesty rule, and an UNCONDITIONAL finalize instruction that is wrong under a runner that owns the transition). SEPARATELY, the declared `Scope-Paths` is redundant (`.aw/records/plans/**` is already implicit) yet not free: an unmodified declared path demands a `--scope-ack`, and `_scope_match` shows the plan's own move into `executed/` does not match the declared `pending` pattern. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate extended with a declaration-style scope fence (explicitly NOT a stop order, with the two genuinely-unsafe stop conditions named), a hard-MUST honesty rule naming this plan's own deliverable and V-03, and a lifecycle paragraph with an unconditional finalize obligation plus conditional runner/executor ownership. The redundancy is recorded as F-13 and in the scope check with the expected one `--scope-ack`, rather than silently deleting a declared path. |
| PR-006 | LOW | IN-SCOPE | A. Correctness | `oc_runipd.dependency_depth`, `simulate_dispatch_order` | "`dependency_depth` sorts it last" is imprecise: depths are `y4bdoz 0`, `1bdxcp 1`, `r9uvwc 1`, `ingpvc 2`, `wfjsp4 3`, so the ORCHESTRATOR dispatches after this plan. Measured order `['y4bdoz','1bdxcp','r9uvwc','ingpvc','wfjsp4']`. The same simulation independently confirms F-08's hazard is live. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to "last among the CHILDREN" with the measured depths and order pasted, an explanation that an `orchestrate` item depends on every child of its Set, and a paragraph separating the sibling missing-edge hazard (owned by `r9uvwc`'s blocking OQ-03 / `PR-001` there) from this plan's own unaffected position. Added as F-14. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's OQ-01 (if E-01 finds the migration ran before placement, stop or record and continue?) is `Blocking: no` and open. Resolve it myself, escalate it, or leave it? | LEAVE IT OPEN, non-blocking, unchanged. | Escalating it to `Blocking: yes`, rejected because the plan's own recommendation (measure, report, file a corrective IPD) is the honest action under either answer, so nothing is gated on the reply; resolving it myself, rejected because the open half is a certification-strictness judgement about how much a partially-correct migration counts as delivered, which is the maintainer's call. | A non-blocking question does not make a plan NO-GO (maintainer ruling 2026-09-10, plan `qhy3i3` OQ-01, recorded in the plan-review workflow). The question's own text states the same action either way. | yes |
| D-2 | E-02's BEFORE listing is unobservable. Weaken the requirement, or find an exact substitute? | EXACT SUBSTITUTE: git reconstruction, with a mandatory label naming the commit. | Dropping the BEFORE half, rejected because it is the Set's primary acceptance evidence; leaving it as-is, rejected because an unobtainable mandatory item invites fabrication, which is the worst outcome for a verification plan. | `git ls-tree --name-only HEAD~1 .aw/records/specs/` verified to render the flat tree; the plan's declared `executed:1bdxcp` edge proves it cannot observe the pre-migration state. | yes |
| D-3 | The coverage-gate overstatement: correct the claim, or also change what the plan does? | CORRECT THE CLAIM ONLY. The plan's action (author the child, add the row, leave the parent's checklist) is exactly what the code's own remedy string prescribes. | Recommending the parent's items be deleted so the probe passes, rejected outright as the documented compliance-by-deletion failure; recommending `--allow-uncovered-orchestrator-work` be pre-authorized here, rejected because that flag requires a human justification and a reviewer must not supply it. | `probe_refusal_remedy` names the constructive action and forbids deletion; the excerpt and prompt were read and the excerpt rendered. | yes |
| D-4 | The citation figures do not reproduce. Substitute my own triple, or require a method? | REQUIRE A METHOD and record all three of my triples as illustrations. | Replacing 51/33/18 with one of my numbers, rejected because that would repeat the plan's own error one commit later: the metric is method-dependent, so a single authoritative-looking triple is exactly what should not be written. | Three enumerations at one commit gave three different triples; the delta rule was already the plan's real instruction. | yes |
| D-5 | The redundant `Scope-Paths` declaration: delete it or document it? | DOCUMENT IT, with the expected `--scope-ack` named. | Deleting the declared path, rejected because it grants nothing but states intent, it matches the parent's justification, and silently narrowing a declaration on a plan devoted to honest reporting is the wrong kind of reviewer edit. | `scope_paths_implicit_allowances` returns `.aw/records/plans/**`; `_scope_match('.aw/records/plans/executed/x.ipd.md', '.aw/records/plans/pending')` is False; the `in_scope_unmodified`/`missing_acks` computation was read. | yes |
| D-6 | Is this plan's existence justified at all, given `r9uvwc` and `1bdxcp` already carry their own `V-*` items? | YES. Justified and not redundant. | Recommending it be retired as duplicative, rejected because the parent's E-02/E-03/E-04 are whole-Set properties no single child can demonstrate, and the retirement path provably skips the one checkpoint that would have caught their absence. | `ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]`'s recorded reason; `retire_orchestrator`'s docstring; the parent's own CID-1..CID-8. | yes |
| D-7 | Did the gate's missing elements warrant a finding, or a silent repair? | A finding (PR-005) AND an in-place repair, per the workflow's Step 4 instruction to add the element and record it. | Silently adding them, rejected because the workflow requires it recorded. | plan-review Step 4 and rubric G; the 2026-09-01 maintainer ruling that a fence is a declaration and not a stop order. | yes |
| D-8 | Is the plan sound overall, and what readiness follows? | SOUND. `APPROVE WITH REVISIONS APPLIED`, readiness `go-pending-approval`. | `NO-GO`, rejected because the only open question is non-blocking, no BLOCKER or HIGH remains unfixed, and the readiness vocabulary reserves `NO-GO` for genuine not-ready conditions rather than for an unsigned clean plan. | Six findings all FIXED; `aw ipd lint --phase review-finalize` reports zero findings; `aw check` delta empty. | yes |

EVERY FINDING IS `FIXED`. No finding was left `OPEN` or `DEFERRED`, so no escalation into a
`- Blocking: yes` question was required and none was added. The plan's pre-existing OQ-01 remains
open and `- Blocking: no` by deliberate decision (D-1), which per the 2026-09-10 maintainer ruling
does not make the plan `NO-GO`. No `Reversible: no` decision was made in this round.
