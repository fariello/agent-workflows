# Review: Group the check findings report by rule and severity so an advisory is not lost in a per-finding enumeration

- Subject-Id: xs557y
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `89aa4c73`, working tree clean. `aw ipd lint --phase author --agent` reported
`clean` before any edit. Suite measured before any edit: `3387 passed, 2 skipped, 3 warnings`.

THE DIAGNOSIS IS CORRECT AND THE TWO DEFECTS ARE REAL. F-01 reproduces by content: the key really is
`key = (title, fix_action)` with `fix_action = d.fix or fix`, and re-running the shipped grouping loop
over the live corpus gives 44 groups for 56 findings over 6 rules. F-03 reproduces exactly and is the
better of the two findings: `badge` is computed for every member and consumed ONLY in the
`dir_str in ("", ".")` branch, so a live `aw check plans` prints ZERO severity badges (measured) while
carrying three tiers. F-05 reproduces verbatim in `docs/cli-human-guide.md` lines 49 and 53. F-04's
title-fragmentation trap reproduces on the two-Drift probe exactly as described. F-08 and F-09 hold:
the machine renderers never enter `HumanRenderer`, nothing in `tests/` pins its check rendering, and
`tests/conformance_matrix.py` is imported by nothing so the golden is inert.

BUT THE PROPOSED FIX DOES NOT WORK, AND THIS IS MEASURED RATHER THAN ARGUED. E-02 specifies the key
`(d.rule, summary_fix)` and claims 19 blocks collapse to 5. Run over the live corpus, that exact key
yields **44 groups for `plans` and 47 for `all`**, against 6 and 8 distinct rules. It collapses almost
nothing. The cause is that `summary_fix` ALSO interpolates per-finding values: for
`check.plan-spec-link-missing` it is `aw ipd set cpi6p3 --from-spec 25kzda`, a different string for
each of 35 findings. Four of eight live rules have a per-finding-varying `summary_fix` (35, 4, 2 and 2
distinct values). So the plan's Goal, its Expected outcome for E-02, and its headline claim are all
unachievable by the mechanism it names (PR-301).

WORSE, THE REPOSITORY ALREADY MEASURED AND RECORDED THIS. Plan `iyilwm` is `executed` (not `reviewed`
as F-12 states), its change has LANDED, and it is what made `summary_fix` interpolate: the fallback now
reads `summary_fix=d.recovery if d.recovery else "inspect artifact frontmatter..."`. Its own
review finding F-17 says in terms that "a recovery that interpolates a path or id6 no longer collapses
N findings of one rule into one summary line", measured 1 line before and 4 after, and a comment it
placed in `doctor.py` warns that "path- or id6-interpolating recoveries will fragment summary counts".
This plan reads that function, cites that plan as a boundary, and does not notice that the landed
change invalidates its key (PR-302).

THE REAL DESIGN TENSION IS UNRESOLVED AND THE PLAN NEVER SEES IT. Keying on the rule ALONE does reach
the goal (6 blocks for `plans`, 8 for `all`, measured), but it would drop 34 of 35 distinct fix commands
for `check.plan-spec-link-missing`, which collides head-on with this plan's own stated principle that
"NO MEMBER IS EVER HIDDEN" and with the `_SCOPE_DRIFT_PATHS_NAMED` precedent it cites. There is a third
design the plan does not consider, which reconciles both: key on the rule and move the `Fix:` line onto
each MEMBER, so 35 findings become one block with 35 named members each carrying its own command. That
is a different rendering contract than E-02/E-03 describe and it is a presentation decision, so it is
escalated rather than chosen for the maintainer (PR-303, blocking OQ-03).

THREE SMALLER PROBLEMS, all fixed in place. F-14 asserts `zosxj4` overlaps "only in `renderers.py`";
in fact `zosxj4` ALSO declares `docs/cli-human-guide.md`, which is a genuine second file collision, and
`zosxj4`'s own review already recorded it from the other side (its PR-A02 names `xs557y` explicitly).
This plan's Scope check and F-14 both deny it (PR-304). F-12 states `iyilwm` is `- Status: reviewed`
with "NO FILE OVERLAP, but a BEHAVIORAL INTERACTION"; it is `executed`, and the interaction is not
benign but fatal (PR-302 covers the fatality; PR-305 the status). And every count in the plan is stale
by roughly a factor of three (19 findings against a measured 56, 5 rules against 6), which matters less
than usual because E-01 already requires re-measurement and says a moved count is not a stop condition
(PR-306).

WHAT SURVIVES INTACT AND SHOULD NOT BE RE-LITIGATED: F-03's badge defect, F-05's two false doc
statements, F-09's absent coverage, and the entire E-04 severity-and-ordering item, which is
independent of the grouping key and is correct as written. A narrower plan doing only E-04 plus E-06's
badge test would be approvable today.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | BLOCKER | IN-SCOPE | A. Correctness / G. Plan executability | Live corpus at HEAD `89aa4c73`: the key `(d.rule, build_remediation(d).summary_fix)` yields 44 groups for `plans` (56 findings, 6 rules) and 47 for `all` (59 findings, 8 rules); `check.plan-spec-link-missing` has 35 findings with 35 DISTINCT `summary_fix` values (`aw ipd set cpi6p3 --from-spec 25kzda`, `aw ipd set hyuos6 --from-spec 7ckptx`, ...) | **E-02'S KEY DOES NOT COLLAPSE ANYTHING AND THE PLAN'S GOAL IS UNACHIEVABLE AS SPECIFIED.** The plan's premise is that `detailed_fix` interpolates paths while `summary_fix` does not, so swapping to `summary_fix` fixes the fragmentation. Measured, `summary_fix` interpolates too: 4 of 8 live rules carry a per-finding-varying value (35, 4, 2, 2 distinct). E-02's Expected outcome ("19 blocks collapsing to 5") and the Goal ("one block per RULE") are therefore both false under the mechanism E-02 names, and an executor following it literally would produce a report essentially identical to today's and could reasonably report success against a re-measured block count that happens to equal the finding count. | C:Medium; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED as blocking OQ-03 together with PR-303, since the correct key cannot be chosen without deciding where the `Fix:` line lives. E-02 annotated with the measurement, its Expected outcome corrected to state the measured result of its own key, and a `Blocked by: OQ-03` note added. NOT fixed on reviewer authority: every candidate key changes what the report SHOWS, which is a presentation contract. |
| PR-302 | HIGH | IN-SCOPE | Step 1 evidence / D. Anti-regression | `doctor.build_remediation`'s fallback: `summary_fix=d.recovery if d.recovery else "inspect artifact frontmatter and schema conformity."`; its in-file comment "path- or id6-interpolating recoveries will fragment summary counts (F-17)"; executed plan `iyilwm` F-17, measured "1 summary line before, 4 after" | **THE REPOSITORY ALREADY MEASURED THIS EXACT FAILURE AND THE PLAN CITES THE PLAN THAT RECORDED IT.** `iyilwm` has LANDED and is the direct cause of PR-301: it made `summary_fix` prefer the finding's `recovery`, which interpolates. Its review recorded the grouping consequence as F-17 and it left a warning comment at the very function this plan reads. F-12 treats `iyilwm` as a future, benign interaction ("if `iyilwm` lands first the group `Fix:` line becomes a better string and the grouping still works"), which is exactly backwards: it has landed and the grouping does NOT still work. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-12 rewritten: `iyilwm` is `executed`, its change is live, and it is the CAUSE of the defect PR-301 measures rather than a compatible neighbour. Its `doctor.py` warning comment and its F-17 measurement are both quoted so the next author cannot re-derive the same wrong assumption. Added F-17 to this plan carrying the 44-group measurement. |
| PR-303 | BLOCKER | UNDER-SCOPE | C. Architecture / F. UX | Measured: keying on `d.rule` alone gives 6 blocks for `plans` and 8 for `all`, reaching the goal, but `check.plan-spec-link-missing` then holds 35 members with 35 distinct fix commands of which a single block-level `Fix:` line can show ONE; the plan's own Deferred section states "NO MEMBER IS EVER HIDDEN" and cites `_SCOPE_DRIFT_PATHS_NAMED`'s "a finding that reports only a number is unactionable" | **THE PLAN'S GOAL AND ITS OWN NO-HIDING PRINCIPLE ARE IN DIRECT CONFLICT AND IT NEVER NOTICES.** Reaching one block per rule requires a rule-only key, which discards 34 of 35 actionable commands for the largest rule; keeping every command requires the fragmenting key PR-301 measures. The plan asserts both goals and resolves neither. A THIRD DESIGN EXISTS that satisfies both and the plan does not consider it: key on the rule for the BLOCK and render the per-member `summary_fix` on each MEMBER line, so 35 findings become one block with 35 named members each carrying its own command. That is a different rendering contract from the one E-02/E-03 describe (block-level `Fix:`), so it is the maintainer's call. | C:Medium; U:Medium-High; S:Low; F:Medium; Overall:Medium-High | OPEN | ESCALATED as blocking OQ-03 with `- Finding: PR-303`, enumerating the three designs with the measured cost of each. E-03's singleton rule is annotated to note it is well defined only under design (a). NOT fixed on reviewer authority: choosing what the report shows a human is a UX and published-guide decision, and `docs/cli-human-guide.md` is in `Scope-Paths` precisely because this changes it. |
| PR-304 | HIGH | IN-SCOPE | C. Architecture / contention | `zosxj4`'s `- Scope-Paths:` includes BOTH `agent_workflows/renderers.py` AND `docs/cli-human-guide.md`; its E-03 edits that guide's sample transcript; its own review history records PR-A02: "concurrent pending plan `xs557y` declares the same `renderers.py` and the same guide and rewrites the SAME `HumanRenderer.render` method" | **THE PLAN DENIES A SECOND FILE COLLISION THAT THE OTHER PLAN'S REVIEW ALREADY RECORDED.** F-14 calls `zosxj4` "THE ONLY REAL FILE OVERLAP" and scopes it to `renderers.py` alone, and the Scope check lists `docs/cli-human-guide.md` as this plan's without qualification. Both plans declare that guide: `zosxj4` E-03 fixes its sample transcript's hint line while this plan's E-06 corrects items 3 and 6. The edits are to different lines and are compatible, so this is a coordination and evidence fact rather than a runtime hazard, but denying it means whichever lands second may be unable to show the clean diff its own validation demands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-14 corrected to name BOTH shared files, quote `zosxj4`'s PR-A02 from the other side, and state the different-lines/compatible conclusion explicitly. Scope check amended to declare the guide as SHARED with `zosxj4`. No `Item-Dependencies` edge added, for the reason the runners' isolation makes it unnecessary. |
| PR-305 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | `iyilwm` resolves to `.aw/records/plans/executed/...` with `- Status: executed`; F-12 states `- Status: reviewed` | F-12 RECORDS A STALE LIFECYCLE STATE for the one boundary plan whose landing actually matters. The other five boundary readings (`tzjtg4`, `wef7yo`, `nwcf8j`, `zosxj4`, `wqiofa`) re-verify exactly as `pending/reviewed` with the declared paths as quoted, so this is a single-row staleness rather than a pattern. It is graded MEDIUM rather than LOW only because the stale row is the one that carries PR-302. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12's status corrected to `executed` with its path, and the five verified rows annotated as re-confirmed at review so a reader knows which were re-measured. |
| PR-306 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | Measured at HEAD `89aa4c73`: `plans` 56 findings / 44 blocks / 44 Next / 0 badges over 6 rules; `all` 59 / 47 / 47 / 0 over 8 rules; severities `plans` 14 error + 42 info, `all` 17 error + 1 warning + 41 info. Plan records 19/19/19/0 over 5 rules and 22/22/22 over 7, with 16 error / 1 warning / 2 info | EVERY COUNT IS STALE BY ROUGHLY 3x, AND THE SEVERITY MIX HAS INVERTED. The plan measured 19 findings dominated by errors; the live corpus has 56 dominated by 42 `info` (35 of them one rule, `check.plan-spec-link-missing`, which did not exist in the plan's census at all). This is graded MEDIUM and not HIGH because E-01 already requires re-measurement at the executor's own HEAD and explicitly says a moved count is expected and not a stop condition, which is good plan design and absorbs most of the damage. It still matters: the plan's argument that an `info` is "lost among fourteen repetitions of an unrelated error" is now backwards, since `info` is the DOMINANT tier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All counts in the Concern, F-01, F-02, F-03, E-01's Expected outcome, E-02's Expected outcome and F-07 re-measured and updated, with the authoring figures kept beside them as history. The Goal's "lost among repetitions of an error" framing corrected to the measured shape (a handful of errors lost among 42 advisories). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-301/PR-303: should the reviewer pick the grouping key and the `Fix:` placement, or escalate? | ESCALATE as one blocking OQ-03 covering both, with three designs and the measured cost of each | Pick the rule-only key (reaches the goal, but discards 34 of 35 commands and contradicts the plan's own no-hiding principle); pick per-member `Fix:` lines (satisfies both, but is a rendering contract change the published guide describes); mark REPLAN (discards a correct diagnosis and a wholly sound E-04) | The two questions are ONE question: the key cannot be chosen without deciding where the fix command lives, because that is what determines whether a rule-only key loses information. Both halves change what a human sees in a documented surface, so the fix bar is Medium-High on usability and functionality and the call is the maintainer's | no |
| D-2 | Is E-04 (badges in both branches, worst-severity-first ordering) affected by the blocker? | No: it is independent and correct as written, and this is stated in the plan so a maintainer can descope to it | Hold the whole plan; split E-04 into its own plan now | E-04 touches the member-line badge and the block ordering, neither of which depends on the grouping key. F-03 is re-measured true (0 badges live) and the fail-safe rank direction matches `artifact_core.drift_exit_code`. Recording this gives the maintainer a cheap option instead of an all-or-nothing choice | yes |
| D-3 | PR-302: does the landed `iyilwm` change mean this plan should be retired rather than repaired? | No: repair the evidence and escalate the design, keep the plan | Retire to `superseded/` and re-author against the post-`iyilwm` shape | The defects (F-01's defeated key, F-03's unreachable badge, F-05's false docs, F-09's absent coverage) are all still live and correctly diagnosed; only the chosen MECHANISM is invalidated. A plan whose findings survive and whose one item needs re-specifying is repaired, not replaced | yes |
| D-4 | PR-304: add an `Item-Dependencies` edge to `zosxj4` for the two shared files? | No: record the shared ownership and rely on the runners' per-item isolation and merge gate | Declare `Item-Dependencies: zosxj4` so ordering is forced | AGENTS.md states the runners isolate each execute item in its own worktree and return changes through the merge-and-revalidate gate, so file overlap is not a runtime hazard; an edge would gate this low-priority followup on an unrelated plan's approval. The edits are to different lines in both files, verified | yes |

### Round 1 close

Four of six findings FIXED in place. PR-301 and PR-303 are left OPEN at BLOCKER and are ESCALATED into
the plan as a single `- Blocking: yes` question (OQ-03) carrying `- Finding: PR-301` and naming PR-303,
per the gate threshold rule, so `aw ipd lint` refuses the plan at every checkpoint until the maintainer
answers. `- Readiness: no-go` is written accordingly.

The two pre-existing open questions were re-verified: OQ-01 remains correctly `resolved` (its rejection
of "summarize the dominant rule" is if anything stronger now that one rule holds 35 of 56 findings),
and OQ-02's key-versus-display distinction remains correct, though its "2 of 7 rules" census is now 1 of
8 and was corrected.
