# Review: report every matched artifact's disposition, orchestrator 7ewc74 (Set runnoop)

- Subject-Id: 7ewc74
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `146905d8`. Structural preflight `aw ipd lint --phase author` conformed CLEAN with no
advisory, and `--phase review-finalize` conforms clean after the revisions.

DISCLOSURE: authored in the same session as the two `runrecon` plans reviewed just before it, so this is a
self-review. The cost is visible in PR-802 and PR-803: two of the plan's cross-cutting constraints (an
import count and a sibling plan's status) were stated as measured facts and were both stale, and CID-1 as
written could not have been satisfied by either true measurement.

THIS IS AN ORCHESTRATOR, so the review applied the orchestrator-specific bar first, and the plan PASSES it.
Its three E-items each confirm a child's terminal state and nothing else: no deliverable, no baseline, no
post-hoc reconciliation is parked on the parent. That matters mechanically, not stylistically, and I
verified the mechanism rather than citing the rule: `ipd_lifecycle.ROLLUP_OMITTED_GATES` names
`pre-transition-ev-checkpoint` as "THE ONE DELIBERATE DIFFERENCE", omitted because an orchestrator's items
are "performed by NOBODY", so any work parked here would be marked complete having never been performed OR
verified. Nothing is. The plan also keeps its child checklist, which is correct: `evaluate_set_retirement`
reads each child's on-disk status, and a Set executed by hand needs that table to run completely and in
order. Measured, `evaluate_set_retirement(Path('.'), 'runnoop')` returns `unfinished-children` naming all
three children with `unauthored_rows: ()`, so the table parses and retirement is properly gated.

THE DEFECT IS CONFIRMED LIVE by executing all five deciding expressions rather than reading them:
`oc.SUCCESS_STATES == agy.SUCCESS_STATES` is True while `is` is False; `'reviewed' in SUCCESS_STATES` is
True; `action_for('child','reviewed')` is `'execute'`; `deliberate_stop_exit_code(["reviewed"],
success_states=SUCCESS_STATES, stopped=False)` is `0`; and calling the REAL `render_run_summary_table` with
one `reviewed` item prints `Outcome: COMPLETED` and `Progress: 1/1 [##########] 100% (1 reviewed)` with
ZERO diagnostic bullets. A green hundred percent for zero work performed, exactly as reported.

WHAT ROUND 1 CHANGED. Nine findings, all FIXED in place; none deferred, none left open, none REPLAN. No
E-item was added or removed: the three-item orchestration checklist was already the right shape. The most
consequential change is PR-801, which STRENGTHENS the Set's warrant and simultaneously removes a decision
the plan had delegated: the shipped behavior does not merely under-report, it violates an approved spec
requirement, and that same spec already fixes the disposition token, so OQ-01 is resolved rather than
handed to a child executor.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | A. correctness; spec obligation | spec `25kzda:484`, `:1035-1042`, `:1099` | **The plan understates its own spec position in a way that left a decided question open.** It says §5.6 "already REQUIRES most of what this Set builds" and tells child 01 to CHOOSE between `needs_input` and a new token, calling both "defensible". Measured against the spec: §3.2's per-status table has a row for exactly this case requiring that a `reviewed` IPD unattended "Stop `needs_input`. Exact recovery names the human approval command", and forbidding "Self-approval or treating model approval as human approval"; §5.6's allowed per-item outcomes are a CLOSED list containing `needs_input` glossed "a human gate stopped the item"; §11 repeats it. `needs-approval` appears nowhere. So the shipped behavior VIOLATES an approved spec, and the token is DECIDED. Leaving it to a child invited the third vocabulary the question itself warned against, and would have put CID-3 (one disposition vocabulary derived from one definition) at the mercy of an executor's choice | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Spec-sync section rewritten around §3.2's prescriptive row and §5.6's closed list, with the violation stated as the Set's warrant. OQ-01 flipped to `resolved` with the three citations and an escalate-do-not-choose instruction. New F-9. New CID-6 pins the token. E-01 now includes confirming child 01 emitted the spec's token. A completion criterion and V-01 updated to demand it. Added the further §5.6/§3.2 obligation the plan had not noticed: the remedy must be the LITERAL human approval command, not a generic pointer |
| PR-802 | MEDIUM | IN-SCOPE | Evidence accuracy; G. executability | `ast.walk` over `agy_runipd.py` | **CID-1 was unsatisfiable as written.** It requires the oc-to-agy import count be "47 before this Set and 47 or lower after"; measured, it is 43 at top level and 48 counting five names that arrive through function-local imports across 8 `ImportFrom` sites. A child asked to prove 47 could not have done so, and the natural workaround (walking only `Module.body`) silently hides the five nested ones | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | CID-1 restated with both counts, the five nested names listed, a requirement to state WHICH count is measured and report before and after, and an explicit instruction to walk the whole tree rather than `Module.body`. The identical figure in the hard-constraints block corrected too |
| PR-803 | MEDIUM | IN-SCOPE | Evidence accuracy; C. architecture | `r2i1b1` front matter and open questions at HEAD | **The overlap fence rests on a stale status, which inverts its practical meaning.** The plan calls `r2i1b1` "`to-review`, blocked on its own OQ-02"; it is now `- Status: approved` with `- Readiness: go-pending-approval`, both open questions `resolved`, and `- Item-Dependencies: none`, so it is RUNNABLE NOW while this Set is not approved. "If `r2i1b1` lands first" is therefore the LIKELY ordering, not a contingency, and CID-5 becomes an authoring instruction for child 03 rather than a validation-time check. Its declared `Scope-Paths` also overlap all three children here | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Fence paragraph rewritten with the current status and the two consequences (check for the record BEFORE authoring; overlap is a review-ordering fact, not a runtime hazard). F-8 corrected. CID-5 restated as expect-it-first. V-03 now says to expect YES |
| PR-804 | MEDIUM | IN-SCOPE | Evidence accuracy; D. anti-regression | `oc_runipd.py:7562`/`:7577` vs `agy_runipd.py:4574`/`:4589` | **The two hosts print DIFFERENT continuation strings and the plan treats them as one.** oc says `No OpenCode session was captured for this run.`, agy says `No Antigravity session was captured for this run.` The plan quotes only the oc wording and calls the agy site its "twin", so a child fixing the footer could pin the oc literal on both hosts, which fails CID-2 while looking symmetric | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-6 records both strings and requires the fix be parameterized on the host label rather than a literal; the completion criterion for the footer updated to say the same. Citations re-resolved (all four had drifted) |
| PR-805 | MEDIUM | IN-SCOPE | Evidence accuracy | regex scan excluding `EXECUTION_SUCCESS_STATES`, each site classified | **The `SUCCESS_STATES` call-site counts are wrong, and one difference between the hosts is load-bearing.** The plan says seven oc sites and five agy. Measured: oc has 8 textual occurrences of which one is the definition and one is inside a comment, leaving SIX real uses; agy has 5 of which one is the definition, leaving FOUR. More importantly the two extra oc uses are both DEPENDENCY sites (`:3377`, `:4275`) with NO agy counterpart, so the hosts are asymmetric on this constant and a child assuming a one-to-one mapping of call sites would mis-plan its classification | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-7 rewritten with both corrected counts, every site enumerated with the question it answers, and the asymmetry named. A new under-scope entry records that this Set does not unify the asymmetry, so it is not mistaken for an oversight |
| PR-806 | MEDIUM | IN-SCOPE | E. testing; G. executability | measured on two executed plans | **V-01 demands a lint phase that cannot pass on the artifact it names.** It asks for `aw ipd lint --phase pre-transition` on child `zz5yxq` AFTER that child reached `executed` and moved to `executed/`. Measured on real executed plans, a terminal-directory file lints as `legacy/not evaluated` under `pre-transition`; `post-transition` is the phase that actually evaluates it. An executor would paste a not-evaluated line as if it were a pass | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now requires `--phase post-transition` with the reason stated, and additionally requires the child's own `needs_input` evidence be cited so the spec-fixed vocabulary is provably what landed |
| PR-807 | MEDIUM | IN-SCOPE | Evidence accuracy | `render_stream.py:1872`, `:2153-2172` | The summary-table finding is right in conclusion and wrong in detail: the COMPLETED tuple holds FOUR statuses, and the diagnostics block is not a "five-status allowlist" but THREE branches covering four statuses, two of which are additionally gated on `driver_error` and one on `interrupt_reason`. That gating is the sharper fact (two allowlisted statuses render nothing even today) and `r2i1b1` already owns it, so describing it as a flat allowlist risks a child here trying to fix it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 rewritten with the real branch structure, the four statuses, the field gating, and a note that `r2i1b1` owns it; the rendered evidence recorded as executed output rather than a description |
| PR-808 | LOW | UNDER-SCOPE | E. testing; release gate | `evaluate_blocking_close` predicate; all three children's front matter | V-03 asks for `em0z50` at `done` and `aw backlog check` clean, but does not ask for evidence the RELEASE GATE was discharged rather than dropped. The item carries `- Blocks-Release: next`, so `aw backlog set done` fails closed unless a plan carrying `- From-Backlog: em0z50` also carries the same gate; all three children do (verified), so the handoff is available, but a hand-edit would bypass it and the V-item as written would not notice | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now requires naming which child satisfied the predicate and pasting the SETTER's output rather than a hand-edit, with the predicate's rule stated |
| PR-809 | LOW | IN-SCOPE | Evidence accuracy; G. executability | every citation re-resolved at HEAD | Citation rot across the plan: `SUCCESS_STATES` (`:327`/`:388` -> `:336`/`:408`), the queue ternary (`:3011`/`:2026` -> `:2979`/`:2012`), the continuation hint (four coordinates, all moved), and the diagnostics block (`:2152` -> `:2153`). Every cited construct exists and every claim about it is true, so this is rot rather than error, but the plan gives children coordinates for files three other Sets are editing and carries no re-locate instruction | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All citations re-resolved. A RE-LOCATE-BY-SYMBOL paragraph added to the gate naming the measured drifts as its justification and listing the symbols to search for. Also added the `render_stream` cycle constraint (it imports zero first-party modules while `runner_shared:136` imports it), which `r2i1b1`'s review had to discover the hard way and which any child siting a shared vocabulary must respect |

No finding was DEFERRED, left OPEN, or marked REPLAN, so no escalation to a `- Blocking: yes` question was
required and the repository's `HIGH` gate threshold is not engaged. PR-801 is the only HIGH and it was
fixed in place because the spec ANSWERS it: reading three sections replaced a delegated choice with a
citation, which needs no human judgement.

OQ-01 was the plan's only open question and is RESOLVED from the approved spec. No new question was raised:
every gap review found was answerable from the repository, and none of the fixes required a maintainer
decision about scope, priority, or risk.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 was open with the child-01 executor as owner: does the new disposition take `needs_input` or a new token? | RESOLVED to `needs_input`, fixed at the parent so no child chooses. | (a) Leave it to child 01 as authored, rejected because the spec already decides it and an executor choice here would put CID-3's one-vocabulary rule at the mercy of that choice. (b) Mint a `needs-approval` token and amend §5.6, rejected as an unnecessary amendment to an approved spec when the existing token's gloss ("a human gate stopped the item") is an exact fit and §3.2 already names it for this row. (c) Escalate to the maintainer, rejected because the repository answers it; escalating a spec-answered question wastes a round trip. | spec `25kzda:484` (§3.2 row), `:1035-1042` (§5.6 closed list), `:1099` (§11) | yes |
| D-2 | PR-803: `r2i1b1` is approved and likely to land first. Restate the fence, or add a dependency edge from this Set to it? | RESTATE the fence as expect-it-first, with no `Item-Dependencies` edge added. | (a) Add `Item-Dependencies: executed:r2i1b1` to child 03, rejected because the two are genuinely independent: child 03 can author its summary whether or not the refusal record exists, and a hard edge would block this Set on another Set's approval and execution for a coordination that a check-before-authoring instruction handles. (b) Leave the stale "to-review, blocked" wording, rejected outright as a false statement about a live artifact that inverts the fence's practical reading. | `r2i1b1` front matter (`approved`, both OQs resolved, no dependencies); its `Scope-Paths` overlap; the runner's worktree isolation | yes |
| D-3 | PR-806: V-01 names a lint phase that cannot pass post-move. Change the phase, or drop the lint requirement? | CHANGE it to `--phase post-transition`, with the reason recorded. | (a) Keep `pre-transition`, rejected because measured on real executed plans it reports `legacy/not evaluated`, which an executor could paste as a pass; a validation that cannot fail is not a gate. (b) Drop the lint from V-01 and rely on the child's own gate, rejected because the parent's only job IS confirming the children's terminal state, so removing its one structural check would leave the item evidence-free. | executed `aw ipd lint` at both phases against two plans in `executed/` | yes |

Nothing in the plan's core reasoning was rejected. Its diagnosis, its three-way decomposition matching the
backlog item's three named defects, its refusal to define a second refusal record or widen any gate, its
orchestrator hygiene (confirmation items only, child checklist retained), and its explicit statement that
this parent's V-items own ONLY orchestration while every substantive criterion belongs to a child are all
correct and were preserved. What review supplied was a spec citation that both strengthens the warrant and
closes the open question, two stale cross-cutting facts corrected, a host asymmetry the children must not
assume away, a lint phase that can actually fail, a release-gate evidence requirement, and a current map of
the code.
