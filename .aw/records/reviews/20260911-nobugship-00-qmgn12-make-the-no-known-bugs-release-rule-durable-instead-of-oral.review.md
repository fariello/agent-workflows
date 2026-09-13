# Review: make the no-known-bugs release rule durable instead of oral, orchestrator qmgn12 (Set nobugship)

- Subject-Id: qmgn12
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `9582c659`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) on this orchestrator AND on all three children before semantic review. At `--phase
review-finalize` the linter now reports one `IPD-Q501` error, which is the escalation gate working as
designed: it is the blocking question this review added, and it is the mechanism by which an unfixed
BLOCKER stops execution rather than merely being reported.

DISCLOSURE: this Set was authored in the same repository by the same model family, so treat this as a
near-self-review worth less than an independent one. Its value rests on what was EXECUTED. Eight things
were measured rather than recalled: the oral-rule grep re-run verbatim across six documents; all five
population counts recomputed from disk; the graduation leak recomputed per-item; the shipped
`check_release_gate_consistency` predicate DRIVEN on the live tree; that same predicate driven again in
a THROWAWAY COPY after backfilling one item, which is how the blocker was found; the gate spelling
tallied across every gated item; the release record's `next` resolution confirmed; and the
terminal-plan edit policy read in `AGENTS.md`.

SCOPE OF THE LEDGER. The invocation named the orchestrator only, so the ledger is that one plan. The
three children (`zqs0px`, `di08i9`, `rgaasb`) were read as EVIDENCE and NOT edited, matching how this
repository reviews a Set (each child carries its own record). The consequence is stated where it
matters: PR-001's remedy lands in child 03's scope and in a shipped rule, so it is escalated rather
than fixed.

THE SET'S THESIS IS CORRECT AND ITS SHAPE IS RIGHT. The rule really is written nowhere: the grep for
"don't ship known bugs", "every bug blocks" and "no known bugs" across `AGENTS.md`, `DECISIONS.md`,
`GUIDING_PRINCIPLES.md`, `.aw/records/backlog/README.md`, `CONTRIBUTING.md` and `RELEASING.md` returns
NOTHING. The graduation leak reproduced EXACTLY as authored: 11 of 11 graduated gateless bugs have a
plan carrying their `- From-Backlog:` and 0 of 11 of those plans carry a gate. Write-it-down,
default-at-creation, enforce-and-backfill is the right three-part answer to the maintainer's question,
and review changed none of it.

THE BLOCKER WAS FOUND BY RUNNING THE SHIPPED CHECKER, NOT BY READING. `check.from-backlog-gate-mismatch`
ships at ERROR severity in the exit-blocking sweep and fires when a `From-Backlog` carrier's gate
differs from its item's. Child 03 CITES that rule family as the precedent for its own registration and
never notices that its own backfill is what trips it. In a throwaway copy of the repo, adding
`- Blocks-Release: next` to one graduated item produced an immediate ERROR against a plan in
`executed/`, which `AGENTS.md` forbids editing in place. Across the population the backfill would newly
flag 13 carriers, 2 of them terminal. So the Set as sequenced cannot reach a clean sweep by any route
it authorizes, and its own completion criterion 4 plus V-02's "paste `aw check backlog` clean" are
unreachable.

THE ROOT CAUSE THE FINDINGS SHARE is that the Set reasoned about the gate as a property of a BACKLOG
ITEM, while the repository already treats it as a property of a HANDOFF PAIR (item plus carrier). Every
correction below follows from that: the collision (PR-001), the missing collision measurement in E-01
(PR-002), the cross-check that tests the new rule in isolation (PR-003), and the completion criterion
that cannot distinguish a gated item from a consistent handoff (PR-004). Two further findings are the
ordinary kind: stale counts, and an unobtainable "clean checker" evidence bar.

WHAT REVIEW CHANGED. One finding is BLOCKER and left OPEN, escalated with four costed options, because
two of those options change a shipped ERROR rule's behavior and choosing is the maintainer's call. Six
were fixed in place. E-items stayed at 2 and V-items at 2 (the parent correctly holds only a premise
check); completion criteria grew 6 to 7; the cross-IPD validation gained the run-both-rules requirement
and the throwaway-copy experiment; the child table now marks Order 03's extra precondition; and the
gate gained a four-item "do not re-inherit" list.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A. correctness; D. domain invariants; G. executability | `check_engine.py:2226-2241` and `:105-124`; `AGENTS.md:63` (terminal-plan edit prohibition); child `rgaasb:7` (`Scope-Paths` lacks the plans tree); measured in a throwaway repo copy | **The backfill violates a SHIPPED ERROR rule, and 2 of the 13 artifacts it puts into violation are immutable.** `check.from-backlog-gate-mismatch` fires when a `From-Backlog` carrier's `Blocks-Release` differs from its item's. VERIFIED BY EXECUTION: backfilling graduated item `t156g1` with `next` in a throwaway copy produced one ERROR naming plan `5wtzqv`, which is in `executed/`. Across the population, gating the 11 graduated gateless bugs newly flags 13 carrier plans, 11 in `pending/` (`1f7xno`, `9kmbr0`, `lyo1tz` all from `cnwy8g`, plus `76w6mq`, `akzy45`, `i1hlgx`, `k9awrq`, `m867ox`, `vdabn5`, `yeh7gc`, `zexed1`) and 2 in `executed/` (`5wtzqv`, `h9cn0y`). AGENTS.md forbids in-place edits to a plan in `executed/`, so the obvious remedy is available for 11 and FORBIDDEN for 2. Child 03 cites this rule family as its own precedent without noticing the collision, and its `Scope-Paths` does not include the plans tree, so it cannot co-update a carrier as authored. Completion criterion 4 and V-02's clean-checker requirement are therefore unreachable | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED to OQ-03 with `- Blocking: yes` and `- Finding: PR-001`; refusal verified mechanically (`IPD-Q501` at line 120, exit 1). Four costed options recorded (co-update-plus-terminal-exemption / narrow the new rule to open+blocked / gate the plans instead / weaken the mismatch rule) with (a) recommended and (d) named as the one to avoid, since it would blunt the very rule class that catches this Set's own leak. Child table marks Order 03's extra precondition; E-02 forbids dispatching it until answered; Under-scope corrected from silence to a stated gap |
| PR-002 | HIGH | UNDER-SCOPE | E. testing; G. executability | E-01 as authored; the 13-carrier enumeration measured at review | **E-01 re-measures the item population but not the CARRIER population, so the Set's premise check cannot see the collision it is about to cause.** The authored item records five counts plus the graduation leak, all item-side. Nothing enumerates the plans and specs carrying those items' `- From-Backlog:`, which is exactly the set `check.from-backlog-gate-mismatch` will flag, nor which of them sit in a terminal directory where no edit is permitted. Child 03 would discover the mismatch mid-backfill, across 22 items, in a shared checkout | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 gained a third measurement: for every item to be backfilled, enumerate EVERY carrier with its own gate and its DIRECTORY, count the terminal ones, and report the table to child 03 explicitly. V-01 now fails the validation if the collision table is absent, since it is the input OQ-03's remedy is applied to |
| PR-003 | HIGH | UNDER-SCOPE | E. testing; D. domain invariants | the authored cross-IPD section; `check_engine.py:2226-2241`; the throwaway-copy experiment | **The cross-check exercises the new rule against child 02's default but never runs it beside the SHIPPED rule it conflicts with, which is the gap that hid PR-001.** Satisfying the new "a live bug must carry a gate" rule on a graduated item is precisely what VIOLATES the existing "carrier gate must match item gate" rule. Testing the new rule alone reports success while the repository-wide sweep is red, so the Set could pass its own cross-check and still leave CI failing | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Cross-IPD validation now requires BOTH rules run over the SAME post-backfill tree state in one command with zero findings from each, and prescribes the cheap throwaway-copy experiment (copy the repo, backfill ONE graduated item, call `check_release_gate_consistency`) before touching the real tree, citing the review's own result as the worked example |
| PR-004 | MEDIUM | IN-SCOPE | A. correctness; G. executability | completion criteria as authored; the 13-carrier measurement | **No completion criterion can distinguish a correctly gated ITEM from a consistent HANDOFF, so the Set could satisfy every criterion while leaving 13 mismatches.** Criterion 5 requires the backfill population to be zero, which is an item-side property; an item can be correctly gated while its carrier is not, and that is exactly what the backfill creates | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New criterion 6 requires that NO new `check.from-backlog-gate-mismatch` finding survives the backfill, states that it is not implied by criterion 5 and why, records the measured 13-carrier/2-terminal figure, and requires the end state be reached without editing a plan in a terminal directory. Old criterion 6 renumbered to 7 |
| PR-005 | MEDIUM | IN-SCOPE | Evidence accuracy | measured at HEAD `9582c659`: 196 / 112 / 68 / 46 / 22, gateless split 10 open, 11 graduated, 1 blocked | **All five headline counts are stale and the backfill population moved in the FAVOURABLE direction, which is its own hazard.** Authored 187/103/60/32/28; measured 196/112/68/46/22. The gateless count FELL from 28 to 22 while the bug count ROSE, meaning other agents have been gating bugs in the interim. An executor quoting 28 would over-report the problem and might "find" six items that no longer need backfilling. The graduation leak, by contrast, reproduced exactly (11 of 11 / 0 of 11) and is the Set's durable finding | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern block carries the full re-measurement with date and HEAD and notes the oral-rule claim still holds exactly. E-01 carries both prior readings and instructs deriving a third. Gate note corrected 28 to 22. Recorded as correction 1 in the gate's do-not-re-inherit list |
| PR-006 | MEDIUM | IN-SCOPE | E. testing; evidence accuracy | measured `check.from-backlog-gate-mismatch` = 0 on the live tree; `aw check plans` carries pre-existing findings unrelated to this Set | **V-02 requires a clean checker, which is either unobtainable or obtainable only by editing another party's artifacts.** "Paste `aw check backlog` clean" gives no baseline and no per-rule delta, and the adjacent `aw check plans` sweep carries pre-existing findings this Set does not cause. An executor could reduce a count by touching other agents' pending plans, which the shared-checkout rule forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-02 now requires a per-rule DELTA against a baseline captured before the first edit, names `check.from-backlog-gate-mismatch` specifically with its measured zero so any post-backfill occurrence is visibly NEW, and forbids reducing a count by editing another party's artifact. A checker baseline requirement was added to the required-tests section alongside the suite baseline |
| PR-007 | LOW | IN-SCOPE | E. testing; documentation sync | measured bare suite at `9582c659`: `5971 passed, 3 skipped, 2 xfailed`; 86 of 86 gated items spell the gate `next`; release `f33nrj` `planned` 2.0.0 | Three smaller gaps: no reference suite baseline to notice a pre-existing failure against; the spec-sync section left "whether the rule is already written" unmeasured when a grep settles it; and the backfill's gate SPELLING was unspecified though every one of the 86 gated items uses the literal `next` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests carries the review-measured baseline labelled reference-only plus the bare-run rule. Spec-sync now records that the grep returns nothing so child 01 ADDS text rather than reconciling a contradiction, and points at the adjacent `AGENTS.md` "Release gates" contract with its `Blocks-Release` versus `Blocked-By` distinction to preserve. Deferred section records the `next` spelling tally so no id6 spelling needs supporting |

PR-001 is DEFERRED-AS-OPEN under the Fix Bar at overall Remediation Risk Medium-High on the
FUNCTIONALITY axis, with a secondary complexity axis, and every element the Bar demands is stated. The
axis is functionality because two of the four remedies change what a shipped ERROR rule reports for
every future case, not only for this Set; complexity is secondary because a third remedy requires
widening a child's declared scope to the plans tree and co-updating eleven artifacts in a shared
checkout. The risk reaches the threshold for two independent reasons: the choice trades a shipped
contract against a backfill and is therefore a policy call, and two affected carriers are in
`executed/` where `AGENTS.md` forbids in-place edits, so no purely mechanical fix exists. The required
decision is the maintainer's choice among OQ-03's four costed options. The consequence of leaving it
unresolved is that child 03 backfills, the sweep turns red with 13 ERRORs, two of them unfixable
without violating the terminal-plan rule, and the Set cannot satisfy its own completion criteria.
Effort, time, cost and tokens played no part in this deferral.

Per the escalation rule the finding is raised in the plan as an open question carrying `- Blocking: yes`
and `- Finding: PR-001`, and the refusal was verified rather than assumed: `aw ipd lint --phase
review-finalize` exits 1 with `IPD-Q501` naming OQ-03 at line 120, so the plan cannot reach `approved`
or `begin` until the maintainer answers.

WHAT REVIEW DID NOT CHANGE, recorded because a reviewer that rewrites a sound design does harm: the
three-part decomposition, the ordering (01 independent, 02 and 03 after it, 03 last), the decision not
to gate other work-kinds without asking (OQ-01), the honest statement that a defect mislabelled `chore`
escapes the gate (OQ-02), the refusal to retrospectively gate `done` bugs, and the choice to have the
Set gate its own release. All were checked and all are correct. The children's `- Item-Dependencies:`
metadata was also left untouched deliberately: the collision is not an ordering problem between
children, so renumbering would misdiagnose it.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001's remedy looks mechanical for 11 of 13 carriers. Fix the pending ones by widening child 03, or escalate the whole thing? | ESCALATE as blocking OQ-03 with four costed options and a recommendation, editing no child. | (a) Widening child 03's `Scope-Paths` myself and prescribing the co-update, rejected because it decides a policy question (whether a terminal carrier is exempt, and whether the shipped rule should become directory-aware) by fiat, and because child 03 was not in the review ledger. (b) Prescribing option (b), narrowing the new rule to `open`/`blocked`, rejected because it leaves 11 real bugs ungated and contradicts the Set's own concern statement. (c) Noting it in the cross-check without escalating, rejected because it fails OPEN: child 03 would backfill and the sweep would go red with two unfixable findings. | `check_engine.py:2226-2241`; `AGENTS.md:63`; child `rgaasb:7`; the throwaway-copy experiment naming `5wtzqv` in `executed/` | yes |
| D-2 | Should the 2 terminal carriers be brought into agreement some other way (a corrective IPD), rather than exempted? | LEFT TO OQ-03, and named inside option (a) as a directory-aware narrowing of the rule rather than an edit. | (a) Prescribing a corrective IPD per AGENTS.md's post-execution-gap rule, rejected as disproportionate: a finished plan's gate is history rather than a live release claim, so the honest fix is for the rule not to demand agreement from a terminal carrier at all, and that is a rule change the maintainer should authorize. (b) Prescribing an in-place edit to the two `executed/` plans, rejected outright: AGENTS.md forbids it explicitly. | `AGENTS.md:63`; the two carriers `5wtzqv` and `h9cn0y` measured in `executed/` | yes |
| D-3 | The gateless population FELL from 28 to 22 between authoring and review. Treat that as invalidating the Set? | NO. Record both readings, require a third at execution, and keep the Set. | (a) Marking the Set REPLAN because its numbers moved, rejected as disproportionate: the thesis (the rule is unwritten) and the durable finding (0 of 11 graduated bugs carry the gate through the handoff) are unaffected, and the direction of movement does not weaken the case for making the rule mechanical. (b) Silently updating the counts, rejected because the AUTHORED reading is evidence of what the corpus looked like when the maintainer asked the question, and deleting it would hide that the drift is ongoing. | recomputed counts 196/112/68/46/22 against authored 187/103/60/32/28; graduation leak identical | yes |
| D-4 | Should review verify the collision by experiment, or is reading the predicate enough? | EXPERIMENT, in a throwaway copy, and require the executor to repeat it. | Reading `check_release_gate_consistency` alone, rejected because the rule's exact firing condition depends on which iterators it scans and whether a missing carrier gate counts as a mismatch, and both are easy to misread; the experiment settled it in one step and produced the specific artifact name (`5wtzqv`, in `executed/`) that makes the finding actionable. Running it against the REAL tree, rejected outright: it would write a gate into a co-worker's backlog item in a shared checkout. | the copy-and-drive experiment; `check_engine.py:2205-2241`; scratch copy removed afterwards and `git status` confirmed clean | yes |

## Round 2


Opened 2026-09-12 to record the maintainer's answers to the three questions round 1 raised. Round 1 is
left exactly as written: the findings gate reads only the CURRENT round, and the reviews README states
rounds are appended rather than edited, so flipping a round-1 cell would hide that the questions were
ever put. NO PLAN CONTENT WAS RE-CRITIQUED and no new finding was derived. No product code was modified.

THE BLOCKING QUESTION WAS ANSWERED BY REFRAMING THE RULE, NOT BY ROUTING AROUND IT, and the maintainer's
own question is what produced the reframing: "So any gate should be that no plan be non-blocking if it
graduated from a blocking backlog item, but why would we care if a plan is blocking but the backlog is
not?"

I MEASURED BOTH DIRECTIONS IN A THROWAWAY CLONE BEFORE ACCEPTING IT, because the reframing only holds if
the asymmetry is real. Gating graduated item `t156g1` produced exactly ONE finding naming carrier
`5wtzqv` in `executed/` (delta +1 from a zero baseline). Adding `- Blocks-Release: next` to pending plan
`yeh7gc`, whose item `5ev6lh` has NO gate, produced ZERO findings. The cause is structural: the
comparison loop only populates `item_gate` for an item that HAS a gate (`check_engine.py:2207-2216`), so
a gated plan under an ungated item is unreachable BY CONSTRUCTION.

SO THE RULE ALREADY IMPLEMENTS THE ONE-WAY OBLIGATION and its name oversells it. What it protects is a
DROPPED HANDOFF: a plan going non-blocking when it graduated from a blocking item. Read that way, a
carrier in `executed/` is a case the rule should NEVER have flagged, since a finished plan cannot drop a
future obligation and has no future release to gate. Flagging it demands an edit `AGENTS.md` forbids in
order to assert a live claim on an artifact with no future.

I TESTED WHETHER THE NARROWING IS PRINCIPLED OR A SPECIAL CASE, which is the objection it would otherwise
attract: `check_engine.py` already ships `_EXECUTED_SEGMENT` (`:999`), an `is_retired` predicate
documented for this purpose (`:483`), 31 references to terminal exclusion, and a NEIGHBOURING rule
excluding `executed/` for the identical stated reason (`:1069-1070`). It follows precedent.


### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness and data integrity / G. Plan executability | round 1's execution-measured collision, re-verified at round 2 in a throwaway clone (+1 finding naming `5wtzqv` in `executed/`) | Carried forward from round 1: BACKFILLING A GRADUATED BUG'S GATE TRIPS THE SHIPPED `check.from-backlog-gate-mismatch` AT ERROR SEVERITY, and 2 of the 13 newly-flagged carriers are in `executed/`, which `AGENTS.md` forbids editing, so the Set could not reach its own completion criterion by any route it authorized. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | RESOLVED BY REFRAMING THE RULE, which is neither of the two routes round 1 favoured. The rule is restated as the ONE-WAY obligation it already implements (a LIVE carrier must not drop a gate its item carries) and SKIPS a terminal carrier, reusing the shipped `is_retired`/`_EXECUTED_SEGMENT` precedent. The 11 live carriers are still co-updated; `5wtzqv` and `h9cn0y` are never touched. OQ-03 carries the ruling, the two measured directions, and an explicit instruction to add a test pinning BOTH so the rule cannot silently become symmetric again. Option (d) (flag only a both-gated conflict) was offered and DECLINED, because it would drop the dropped-handoff detection that is the rule's entire purpose. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | OQ-01: should `security` auto-gate the next release as `bug` now does? | NEITHER globally: make the gating work-kind set CONFIGURABLE per repository, defaulting to `bug` ALONE. Carried by backlog `0htqmm`; this Set does not implement it. | Gate `security` globally (declined: the maintainer has measured agent security classifications in THIS repo to be overstated, since an agent assumes an adversarial actor and "an adversarial agent can in fact overcome ANY security we put in place"); leave it ungated globally (declined: for most of their OTHER projects every security finding genuinely must block); gate `security`+`high` only (declined: makes the written rule two-dimensional, which defeats a Set that exists to state one rule plainly); default the new key to `bug`+`security` (declined: wrong for the very repo doing the configuring, and a default the reference repo must override is a bad default). | The `review_findings_gate` precedent (`config.py:1085-1104`): same problem shape, same file, unknown keys round-trip via `unknown_fields`, default documented. One live `security` item (`754txs`) measured, already carried by a plan. | yes |
| D-2 | OQ-02: does a defect filed as `chore` escape the gate, and is that acceptable? | YES it escapes, and it is acceptable WITH THE LIMIT STATED IN WRITING. No mechanism added. | Add a reviewer-side audit of every `chore` (declined: a second classification pass with the same judgement problem one layer down); claim the gate is complete (declined: it demonstrably is not). | Measured the SAME DAY: `59t9x5` was filed `chore` because output was correct, then reclassified `bug` and gated by the maintainer. The mitigation is their perceptibility test, which makes the judgement measurable rather than a vibe. | yes |
| D-3 | Should the auto-gate config be one work-kind key or a general all-gates object? | ONE key, work-kinds only. | A general `gates` object covering the inefficiency perceptibility test and future gates (declined by the maintainer: designs a surface before a second real case exists). | Maintainer ruling 2026-09-12; the perceptibility test stays prose in `zqs0px`'s written rule. | yes |
