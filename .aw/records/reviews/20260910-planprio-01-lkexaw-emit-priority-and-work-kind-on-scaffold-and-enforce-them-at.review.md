# Review: emit Priority and Work-Kind on scaffold and enforce them at the ready-to-execute gate, child lkexaw (Set planprio)

- Subject-Id: lkexaw
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `bf5bbe5a`. `aw ipd lint --phase author --agent` CONFORMED (`outcome:clean, findings:0`)
before semantic review. Bare suite measured before any edit: `5971 passed, 3 skipped, 2 xfailed in 60.94s`.

SELF-REVIEW DISCLOSURE: the same agent and model family authored this Set, so this is closer to a
self-review than an independent one and is worth less. Its value therefore rests on what was EXECUTED
rather than re-read: seven of the plan's claims were tested by applying its own changes to the tree and
running the suite, which is what produced findings PR-002 through PR-010.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS DESIGN IS RIGHT. The scaffold really never emits either field
(`ipd_authoring.py:158-185`), nothing really enforces them, mirroring the `Scope-Paths` gate really is
the right pattern, and the refusal to add either field to `META_REQUIRED` is not merely prudent: applying
that forbidden change and counting produced 109 of 120 pending and 470 of 470 `executed` plans in
`disposition: error`. None of that was changed.

WHAT THE PLAN GOT WRONG IS UNDER-DECLARED SCOPE. As authored it breaks six tests in three files it does
not list, and it selects a sentinel that two SHIPPED rules reject. `Scope-Paths` grew from six paths to
eleven, and two new E-items (E-08 templates, E-09 enum admission) were added, because `aw ipd finalize`
refuses to complete without a `--scope-reason` per out-of-scope path.

THE ONE BLOCKER IS INHERITED AND SITS ON DISK. The parent (`d0cbt3`) records a maintainer ruling of
2026-09-12 reversing this Set's order so Orders 02 and 03 run FIRST, and stating that Order 01's edges
"must be rewritten to depend on 02 and 03". Measured: this plan still carries `- Item-Dependencies: none`
and both siblings still carry `executed:lkexaw`, the overturned direction. Escalated as blocking OQ-02
because the fix spans three other plans' files and is the Set owner's act, not this child's.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | C. Architecture and operability / dependency sequencing | `.aw/records/plans/pending/20260910-planprio-00-d0cbt3-...ipd.md:122` (Ruling 1); this plan `:8`; sibling `8u6770:8`; sibling `lc4unl:8`; `ipd_lint.py:904-913` | The parent's maintainer ruling REVERSED the Set order (02 and 03 before 01), but all three children still encode the overturned direction: this plan carries `Item-Dependencies: none` while both siblings carry `executed:lkexaw`. Measured: 25 pending plans are at the ready-to-execute tier and 18 carry neither field, so executing this plan first makes those 18 unrunnable at EVERY lint phase. `queue_sort_key` sorts on `dependency_depth` first and would faithfully run this plan before the siblings that declare it as prerequisite. | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | Escalated as blocking OQ-02 on the plan. NOT fixed in place: the correction spans three files belonging to other plans plus the parent's child table, only this plan was in the scope ledger, and a cross-plan reordering is the Set owner's decision. Recommendation recorded: confirm the reversal. |
| PR-002 | HIGH | UNDER-SCOPE | E. Testing / declared scope | `tests/test_ipd_templates.py:33-61`; measured `2 failed, 5969 passed` | E-01 as authored lands a two-test regression it does not declare: both IPD templates are asserted BYTE-EQUAL to `build_skeleton`'s output, and neither template nor a regeneration step was in `Scope-Paths`. Measured by applying E-01 and running the full suite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-08 (regenerate both templates, do NOT edit the test) with V-08; declared both template paths; recorded the byte-parity convention in Project conventions. |
| PR-003 | HIGH | UNDER-SCOPE | A. Correctness / cross-surface consistency | `check_engine.py:2646-2693`, `:2700-2755`; driven at review | The sentinel the plan is built around is REJECTED by two shipped rules: `grandfathered`, `unresolved` and `TODO` are each flagged `check.priority-invalid` and `check.work-kind-invalid` at `severity=error`. So the exemption would pass the new lint gate and add two errors per exempt plan on the sweep surface. This is the parent's Completion criterion 4. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-09 (admit only the sentinel, derived from E-02's single constant, with `TODO` still refused) with V-09; declared in Scope and Concern. |
| PR-004 | HIGH | UNDER-SCOPE | E. Testing / declared scope | `tests/test_ipd_priority.py:154-169`; `tests/test_work_kind.py:212-235`, `:362-377`, `:425-443`; measured `4 failed` | E-07 as authored breaks four tests in two undeclared files. The most constraining is `test_the_cli_choices_match_the_shared_vocab`, which pins the choices for `("ipd","set")` AND `("specs","set")` in ONE assertion, so the two verbs cannot diverge without splitting it. Measured by applying E-07 and running the two files. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | Both files declared; all four tests named in E-07 with their guarding intent (preserve the `- Kind:` survival assertion, split rather than delete the shared assertion); `aw specs set` explicitly out of scope; V-07 now demands the split be shown by diff. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness / write-path agreement | `releases.py:434-449`, `:455-474`; driven at review | E-01's prescribed field position ("after `Order`") does not survive the first setter call: both shipped line writers anchor after `- Status:`, so one `aw ipd set --priority ... --work-kind ...` MOVES both lines. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now emits after `- Status:` with the reason stated; re-anchoring the shared writers explicitly rejected (they serve `aw specs set`); V-01 gains a position-stability proof. |
| PR-006 | MEDIUM | IN-SCOPE | D. Anti-regression / honest claims | `ipd_lint.py:1028`, `:1052-1053`; driven at five phases | The terminal exemption is not total, and V-03 demanded proof of a false claim. An `executed/` plan is `legacy` (0 diagnostics) at `author`/`review-finalize`/`pre-execution`/`pre-transition` but IS evaluated at `post-transition`, where 114 of 470 `executed` plans already error. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03, E-06 and V-03 now name the four exempt phases, state `post-transition` as the documented exception, and require the 114 baseline be shown unchanged. |
| PR-007 | MEDIUM | UNDER-SCOPE | F. Principles / self-consistency | `ipd_authoring.py:100-119`; driven at review | The new sentinel would be invisible to the draft-readiness predicate: a fully-authored plan carrying it returns `authoring_placeholders_resolved == True`, so `check.ipd-draft-ready-to-review` would nudge an UNTRIAGED plan toward `to-review`, inverting the very `Item-Dependencies: unresolved` reasoning E-01 cites as precedent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as E-06 case 3 with the lock-step comment cited; recorded in Project conventions. |
| PR-008 | LOW | IN-SCOPE | C. Operability / severity semantics | `artifact_core.py:405-415` | E-04 describes `warning` as a softening, but `drift_exit_code` exempts ONLY `info`, so `warning` fails the gate exactly as `error` does. The sibling `lintreach` plan recorded the identical trap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires stating whether `info` or `warning` is meant and measuring the exit code unpiped; V-04 demands it. |
| PR-009 | LOW | IN-SCOPE | G. Executability / decidability | `20260828-pqsx96-01-...spec.md:129-144`; `check_engine.py:160-170`, `:247-259` | E-04 deferred the invariant-id choice to the executor, but the answer is already determined and citable: no catalog invariant covers triage metadata, and both sibling enum rules are registered with `invariant=""` under a convention stated in place. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now names `""` with the citation and forbids adding a catalog entry (an undeclared spec amendment). |
| PR-010 | LOW | UNDER-SCOPE | G. Executability / spec sync | spec `:449` (Section 9.2 row); `aw specs check` exit 0 measured pre-edit | E-05 named only the Section 4.4 enumeration, but Section 9.2's checkpoint table states the same conditional requirement in full, including the status-tier clause E-03 mirrors. Separately, `aw specs check` already exits 0, so it cannot evidence the amendment's content. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now amends both sections; V-05 requires the diff as content evidence and an explicit statement that the checker proves only non-breakage. |
| PR-011 | MEDIUM | IN-SCOPE | Project rule: no stale measurement | this plan's Concern and F-1 as authored; recounted at review | Four population figures were stale and one was FALSE. "0 of 104 pending plans carry either" is wrong: 11 of 120 now carry both. "all 180 backlog items" is wrong: 197 of 197. The thesis survives; the numbers did not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-1 re-measured with HEAD cited and an explicit instruction not to re-quote; a Required tests section now lists the three pre-existing figures an executor must not mistake for its own regressions. |
| PR-012 | MEDIUM | IN-SCOPE | G. Executability / unsatisfiable evidence | `aw check plans` measured `findings 140`, exit 1 | E-04's evidence requirement implied a clean sweep. Measured bare: 140 pre-existing findings, none attributable to this Set. An executor told to make that clean would either stall or edit other agents' plans in a shared checkout. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 and V-04 now require a self-measured baseline, forbid requiring a clean run, and forbid reducing the count by editing another party's plan. |
| PR-013 | LOW | IN-SCOPE | Project rule: plan gate completeness | this plan's gate section as authored | The gate lacked the lifecycle-move instruction (`aw ipd finalize`, not a raw `git mv`) that sibling plans in this Set carry, and its hazard note quoted the stale corpus figures. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: status/readiness stated, finalize route added, hazard note re-quantified from measurement, and six named corrections listed so they are not re-inherited. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's OQ-01 asked whether the scaffold sentinel should differ from the grandfather sentinel, and deferred it to the executor. Should the review resolve it? | RESOLVE IT: yes, two distinct tokens (`unresolved` for untriaged, `grandfathered` for pre-cutoff), because they are different claims with different gate behavior (refuse vs advisory-pass). | Leave it open for the executor (rejected: measurement showed EITHER choice requires two edits the plan did not have, E-09 and the placeholder addition, so leaving it open would have hidden two scope items). Collapse to one token (rejected: an untriaged new plan would be indistinguishable from a deliberately exempt old one, destroying the audit property the sentinel exists for). | The shipped `Item-Dependencies` precedent distinguishing `unresolved` from `none` (`ipd_schema.py:167-176`) and `Scope-Paths` using `grandfathered` (`:154-157`); the two consequences measured by driving `check_plan_priority`/`check_plan_work_kind` and `authoring_placeholders_resolved`. | yes |
| D-2 | E-01 said to position the fields "after `Order`". Keep the authored position or change it? | CHANGE to "after `- Status:`", matching the shipped writers. | Keep "after `Order`" and re-anchor `releases.set_priority_line`/`set_work_kind_line` (rejected: both writers are shared with `aw specs set`, where the field is genuinely optional, so re-anchoring is a wider behavior change than this plan declares). Keep it and accept drift (rejected: measured, the first setter call moves the line, so the scaffold position is fictional). | `releases.py:434-449` and `:455-474` anchor after `- Status:`; measured by scaffolding at the authored position and running one setter call. | yes |
| D-3 | PR-004 requires the shared choices assertion to change. Should `aw specs set` also drop the `-` sentinel so the one assertion stays undivided? | NO: change the plan verb only and split the assertion. | Remove `-` from both verbs (rejected: `Work-Kind` stays genuinely OPTIONAL on a spec, so clearing it there is a legal end state; the maintainer's 2026-09-10 ruling covered the backlog and plan verbs, not specs; and the parent `d0cbt3` already records this asymmetry as a deliberate, reasoned cost). | `tests/test_work_kind.py:212-235`; the maintainer ruling quoted in `b5sfwm` OQ-02; the parent's Deferred section. | yes |
| D-4 | E-04 asked the executor to judge invariant-catalog fit. Which invariant id? | `""` (empty), with the reason recorded. | File under I-12 (rejected: I-12 is specifically the draft-to-`to-review` authoring nudge, not triage metadata). File under I-09 (rejected: that is the exact misfiling `check.setid-collision` is recorded as, and the convention comment calls a neighbouring id "a false trace"). Add a new catalog entry (rejected: that is a spec amendment this plan does not declare). | Catalog I-01..I-16 read in full (`pqsx96` spec `:129-144`); the convention at `check_engine.py:160-170`; both sibling rules registered `""` at `:247-259`. | yes |
| D-5 | Should this review fix PR-001 by rewriting the three children's `Item-Dependencies` lines to match the parent's ruling? | NO: escalate as blocking OQ-02 and leave every file untouched. | Rewrite all three plus the parent's child table (rejected: three of the four files belong to other plans, only `lkexaw` was in the scope ledger, and the shared-checkout rule forbids editing another party's in-flight work). Note it as prose without escalating (rejected: a prose note gates nothing, and `IPD-Q501` is the mechanism that actually stops execution). | The scope-ledger rule in `plan-review.md:47-52`; AGENTS.md shared-checkout rule; `IPD-Q501` firing measured after the escalation. | yes |

## Round 2

Opened 2026-09-12 to close PR-001, whose escalated question the maintainer CONFIRMED and whose fix has
now been applied. Round 1 is left exactly as written, per the reviews README: the gate reads only the
CURRENT round, and rewriting the earlier cell would erase the fact that the contradiction was caught
here. No plan content was re-critiqued in this round, and no product code was modified.

ROUND 1 WAS RIGHT ON THE FACTS AND RIGHT TO REFUSE THE FIX. The contradiction it found was real and was
an omission by the agent that recorded the maintainer's RULING 1 earlier the same day: the parent's OQ-02
and both siblings' resolutions all SAID the `executed:lkexaw` edges were inverted and must be removed,
and NO FILE'S DEPENDENCY DATA WAS REWRITTEN. Prose said one order; the machine-readable graph still
encoded the other. Its refusal to fix it mid-review was also correct, since four files across three plans
is a cross-plan edit no child declares in `Scope-Paths`.

WHAT WAS APPLIED, by the Set's owner as a records fix at the maintainer's direction, through the tooled
verb rather than by hand (`aw ipd dependencies set`, which canonicalizes and validates before writing):
this plan gained `- Item-Dependencies: executed:8u6770, executed:lc4unl`; `8u6770` and `lc4unl` both
dropped to `none`; and the parent's child table `Depends on` column was inverted to match.

VERIFIED BY THE RUNNER'S OWN SCHEDULER RATHER THAN BY INSPECTION, which is the evidence that matters
because the whole defect was a graph that disagreed with its prose: `oc_runipd.dependency_depth` over the
corrected edges returns `8u6770` 0, `lc4unl` 0, `lkexaw` 1, and sorting by depth yields
`['8u6770','lc4unl','lkexaw']`. The queue now executes the backfills first and this plan last.

THE `Order` NUMBERS ARE DELIBERATELY UNCHANGED, and the parent's table now states that explicitly,
because it is the misreading this correction invites: `Order` is the authored numbering and is no longer
the execution order, while `Depends on` is authoritative. Renumbering would rewrite three filenames and
every cross-reference in the Set for a cosmetic gain.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness / G. Plan executability | round 1's measurement, re-verified at round 2: all four files encoded the overturned order; `dependency_depth` now returns 0/0/1 for `8u6770`/`lc4unl`/`lkexaw` | Carried forward from round 1: THE PARENT'S RULING REVERSED THE SET ORDER AND ALL THREE CHILDREN STILL ENCODED THE OVERTURNED DIRECTION, so a runner sorting by dependency depth would have run this plan FIRST and stranded the 18 approved plans the ruling exists to protect. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | THE REVERSAL IS CONFIRMED AND THE GRAPH NOW MATCHES IT. Option (a) applied by the Set's owner as a records fix at the maintainer's direction: three `- Item-Dependencies:` lines rewritten via `aw ipd dependencies set`, and the parent's child table inverted. Proven with the runner's own `dependency_depth`, not by reading the files. OQ-02 is `resolved` and carries the applied change, the scheduler evidence, an explicit note that `Order` numbers are NOT the execution order, and a standing instruction to STOP if this plan ever becomes executable while a sibling is unexecuted, since that would mean the edge was lost again. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Fix the four files as a records correction, or make the reordering an execution step in the parent? | RECORDS CORRECTION, by the Set's owner, at the maintainer's direction. | An E-item on the parent orchestrator (rejected by the maintainer as unnecessary ceremony for a metadata correction that carries no risk and can be proven immediately); renumber the `Order` fields to match execution order (rejected: rewrites three filenames and every cross-reference for a cosmetic gain, and `NN` is a stable authored identifier rather than a sequence promise). | Maintainer direction 2026-09-12; `dependency_depth` output before and after. | yes |
