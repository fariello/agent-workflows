# Review findings: plan nllamb

- Subject-Id: nllamb
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-701 (HIGH, open, escalated as OQ-03), PR-702 (HIGH, fixed), PR-703 (HIGH, fixed), PR-704 (MEDIUM, fixed), PR-705 (LOW, fixed)

## Round 1

Reviewed at HEAD `657e6278` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review.
The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. At
`--phase review-finalize` the linter now reports ONE finding, `IPD-Q501` on the blocking question this
review raised; that is the intended fail-closed state described below, not an unrepaired structural fault.

THE DIAGNOSIS IS EXCELLENT AND I CONFIRMED ALL OF IT. This plan corrected its own backlog item on two
points and both corrections hold. Re-measured independently:

- F-01 exactly: all 15 ruled id6 are in `executed/`; `m7gvuz` alone carries `medium`/`bug`/`next`;
  `xdr83v` carries `Blocks-Release: next` with no `Work-Kind` and no `Priority`; the other 13 carry none
  of the three.
- F-03 and F-04 verbatim. `stale_record_scope_paths(repo, lc4unl_text)` returns `[]`, and `lc4unl`'s
  front matter does read `- Scope-Paths: .aw/records/plans/pending`. Rewriting that to name one ruled
  target as a pending FILE yields exactly
  `StaleScopePath(path='.aw/records/plans/pending/...hp9rot...', classification='moved-terminal', resolved=('.aw/records/plans/executed/...hp9rot...',))`.
  The `if target.exists(): continue` branch is the measured blind spot, as claimed.
- F-05 on a NON-VACUOUS lookup, which I had to fix in my own probe before trusting it: the `Item` field
  is `id`, not `id6`, and my first attempt silently matched nothing. Corrected, all 15 ruled ids are
  found in a 1985-item scan, every one `native='executed' class='done'`, and `xdr83v` reports
  `blocks_release='next' in_blockers=False` against 257 total blockers. So the conclusion stands on a
  lookup proved to resolve.
- F-02, F-06, F-07, F-08, F-09 and the `ipd_lifecycle._scope_match` grammar all as described. The item's
  `check.bug-without-release-gate` genuinely does not exist and `check.live-bug-ungated` does, so F-06's
  correction of the item is right and worth having made.
- The corpus population is real: 48 executed, 5 pending, 6 superseded plans declare an existing
  `.aw/records/` directory as a scope entry (F-04 recorded 47/5/6; executed has grown by one).

WHAT STOPS THIS BEING AN APPROVAL IS THE RULE HALF, and it took prototyping rather than reading to find.
I implemented E-02's algorithm as specified and measured three things.

FIRST, IT IS COMPUTATIONALLY INFEASIBLE. Step (3) calls `selectors.resolve(repo_root, "plans", id6,
allow={MATCH_ID6})` once per candidate token per pending plan. That call costs about 154ms warm (171ms
cold) because it walks the plans tree. This plan's own `## Detailed Implementation Checklist` yields 92
candidate tokens, which is roughly 14 seconds for ONE plan. A faithful prototype over the 150-plan
pending corpus DID NOT FINISH IN 28 MINUTES, and a 20-plan sample with an `lru_cache` bolted on did not
finish in 18. E-03 wires the rule into `check_types`' full-sweep block, so that cost lands on every
`aw check` and `aw check all` an operator waits on. By this repository's own rule that user-perceptible
inefficiency IS a defect, shipping this introduces a bug while fixing one.

SECOND, THE TOKEN EXTRACTOR IS UNSOUND. An id6 is six lowercase alphanumerics
(`artifact_core.ID6_RE` is `\A[0-9a-z]{6}\Z`), which is also the shape of thousands of English words.
The 92 tokens extracted from this plan's checklist include `across`, `action`, `append`, `around`,
`assert`, `author`, `before`, `blocks`, `caller`, `cannot`, `change`, `choose`, `chosen`, `copies`,
`corpus`, `counts` and `covers`. They are harmless only because they fail to resolve, which means the
unsoundness is absorbed by paying a 154ms filesystem walk per English word. That is the same defect as
the first, seen from the other end.

THIRD, AND THIS IS WHAT MAKES OQ-02 A LIVE BLOCKER RATHER THAN AN EXECUTION DETAIL: the rule fires
SIXTEEN TIMES ON THIS VERY PLAN. After the checklist-only restriction and the own-id exclusions, the
predicate returns the 15 ruled ids plus `lc4unl`, every one resolving into `executed/` and none in
`nllamb`'s `Scope-Paths`. Every one is a false positive: this plan CITES them and writes none of them.
E-02's Constraints say "if that restriction still yields findings on plans that only cite, REPORT THE
COUNT AND STOP", so the stop condition is already met, at review rather than at execution, and OQ-02's
reasoning that the question is "answered INSIDE this plan's execution" is spent. I escalated it as OQ-03
with `- Blocking: yes` and `- Finding: PR-701`, which `IPD-Q501` now enforces at every checkpoint.

TWO FINDINGS WERE FALSE AND ONE OF THEM IS LOAD-BEARING. F-10 records the baseline as "32 findings and
exits 0, i.e. every finding is `info`-class". Measured: **51 findings and exit 1**, with 16 non-`info`
(`check.ipd-uncarried-obligation` 10 at `error`, `check.lifecycle-transition-invalid` 3 at `error`,
`check.name-nonconformant` 2 at `error`, `check.scope-path-target-stale` 1 at `error`,
`check.system-layout-missing` 1 at `warning`). E-03's expected outcome and V-03 both require the before
and after exit codes to be identical and describe the base as 0, so an executor comparing against 0
would conclude their own change broke the gate. And F-11's precedent is stale in a way a careful reader
would hit as a contradiction: `check.ipd-uncarried-obligation` is registered `error` TODAY, directly
beneath a comment block that still reads "WHY THE STAGED TIER IS `info` AND NOT `warning`". It shipped
`info` as the plan says and was later promoted; the live `info` precedent to cite is
`check.ipd-carrier-finished-unverified`.

WHAT I AM NOT FLAGGING, because I checked and it is right. The refusal of the item's option (b) is
correct and unusually well established, resting on three independent measured grounds (F-05's
blocker-set exclusion, F-09's absent tooled path, F-08's D156 prohibition), and D156's text authorizes
E-05(b)'s single pointer line in the exact words the plan quotes. The decision to scope `d0cbt3` by full
path rather than by directory, with the reasoning that declaring `.aw/records/plans/executed` would be
the very bare-directory defect the plan is about, is the kind of self-consistency that is easy to get
wrong. The `0szu1p` carrier for OQ-01 was filed at authoring and deliberately NOT pointed at `iguvci`
(the item this plan closes), which is precisely the obligation-loss reasoning the plan exists to fix,
applied to itself.

NO SPEC AMENDMENT IS OWED and the plan's own spec-sync section argues that correctly: the new rule's
invariant would be `""` following `check.scope-path-target-stale`'s recorded precedent, and claiming
I-07 would misdescribe a declaration fence as a release gate. I verified `check.scope-path-target-stale`
is registered with an empty invariant.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | C. Architecture / E. Testing (a rule that cannot ship as specified) | Prototyped E-02 as written. `selectors.resolve(plans, id6)` = 171ms cold / 154ms warm; 92 candidate tokens from this plan's checklist; corpus prototype over `pending/` killed unfinished at 28 min; 20-plan `lru_cache`d sample killed unfinished at 18 min. Predicate returns 16 findings on `nllamb`, all plans it merely cites | **E-02 is infeasible, unsound, and noisy, and its own stop condition is already met.** The per-token resolve would add roughly ten or more minutes to every `aw check` run (E-03 wires it into the full sweep), which this repository's own perceptibility rule classes as a defect; the bare six-char scan matches ordinary English (`across`, `author`, `blocks`, `corpus`); and after every specified restriction it fires 16 times on this plan with a 100 percent false-positive rate. A rule that fires on correct work is worse than the gap it closes | C:Medium-High; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | NOT FIXED BY THE REVIEWER, because the remedy is a design choice the maintainer owns and the alternatives are materially different products. Escalated into the plan as OQ-03 carrying `- Blocking: yes` and `- Finding: PR-701`, which `IPD-Q501` now enforces at every lint checkpoint (verified: disposition went clean -> `findings` at `review-finalize`). New F-13 and F-14 record all measurements. E-02's Constraints carry a DO-NOT-IMPLEMENT block naming the three defects and the single-inventory-pass requirement; E-03 is marked blocked with it; V-02 now demands wall-clock cost and this plan's own finding count as evidence. Three options stated for the maintainer: re-specify around one inventory pass plus a declaration-based signal, descope to the recording half, or let `0szu1p` subsume it |
| PR-702 | HIGH | IN-SCOPE | Evidence accuracy (a false baseline that inverts a validation bar) | `python3 -m agent_workflows check all` exits **1**; `--agent` reports `"exit":1,"findings":51`. Per-rule: `plan-spec-link-missing` 31 (info), `ipd-uncarried-obligation` 10 (error), `lifecycle-transition-invalid` 3 (error), `ipd-lint-diagnostic` 2 (info), `name-nonconformant` 2 (error), `ipd-carrier-finished-unverified` 1 (info), `scope-path-target-stale` 1 (error), `system-layout-missing` 1 (warning) | **F-10 records "32 findings and exits 0, i.e. every finding is `info`-class"; the gate is RED at 51 findings with 16 non-`info`.** This is not a stale count but an inverted premise: E-03's expected outcome and V-03 both require before and after exit codes to be identical and describe the base as 0, so an executor measuring 1 would reasonably conclude their own change broke CI and start debugging a non-defect | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-10 rewritten with the measured 51/exit-1 baseline, the full per-rule tally with each registered severity, and an explicit statement that the correct bar is an unchanged exit code and unchanged non-`info` finding SET re-derived at the execution base, not a comparison against 0. E-03's expected outcome and V-03 both restated to expect 1 |
| PR-703 | HIGH | IN-SCOPE | Evidence accuracy (a precedent that has since been promoted) | `RULE_REGISTRY["check.ipd-uncarried-obligation"]` is `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`, sitting directly beneath a comment reading "WHY THE STAGED TIER IS `info` AND NOT `warning`". `RULE_REGISTRY["check.ipd-carrier-finished-unverified"]` is `"info"` | **F-11 cites `check.ipd-uncarried-obligation` as the live `info` precedent and it is registered `error` today**, contributing 10 error findings to PR-702's red baseline. The mechanical half of F-11 is exact and confirmed, so the `info` choice for a new rule remains right; what is wrong is the exemplar, and a reviewer checking it would find the rule contradicting its own comment | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 rewritten to separate the confirmed mechanism from the stale precedent, recording that the rule shipped `info` and was later promoted, that its comment now contradicts its registration, and that `check.ipd-carrier-finished-unverified` is the accurate live `info` precedent. E-03's expected outcome names it |
| PR-704 | MEDIUM | IN-SCOPE | G. Plan executability (a stale deferred-question rationale) | OQ-02's rationale reads "This question is answered INSIDE this plan's execution ... either the number is acceptable and the rule ships, or the maintainer narrows it or abandons it". Review measured the number: 16 findings on this plan, all false positives | **OQ-02 defers to execution a judgement whose triggering measurement is now in hand**, so leaving it `open` with that rationale would let an executor reach E-02, re-measure, and stop with no recorded decision, having spent the turn. The question was correctly anticipated; its deferral is what expired | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A dated review note appended to OQ-02 recording that its stop condition is already triggered, that the number is 16 on this plan, and that it is superseded in practice by OQ-03 which carries the same decision with the measurements attached. OQ-02's original text left unedited, because it correctly anticipated the risk and is the record of why the stop instruction existed |
| PR-705 | LOW | IN-SCOPE | G. Plan executability (an unverified documentation target) | `grep` for `Priority`/`Work-Kind` in `.aw/records/plans/README.md` returns nothing; its sections are `## Readiness status (front-matter)`, `## Durable carrier vocabulary`, `## Identity, sets, and the clustering filename grammar`, `## The plans manifest and weekly shards`, `## Execution contract in every plan's gate` | **E-05(a) says to add the paragraph to "the section that already owns plan front-matter contracts", and no section covers `Priority`/`Work-Kind` at all.** The nearest home is `## Readiness status (front-matter)`, which owns `Status` rather than the two fields in question, so an executor is left choosing a section or inventing one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded here rather than by editing E-05, since the instruction is achievable and the ambiguity is small: the reviewer verified `## Readiness status (front-matter)` is the only front-matter section and is an acceptable host, and the finding exists so the executor does not search for a section that does not exist. No plan edit was needed beyond this record |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-701: E-02 is measured infeasible and noisy. Re-specify it myself, descope it, or escalate to the maintainer? | ESCALATE as a `Blocking: yes` open question; change no design | (a) Re-specify E-02 in place around a single inventory pass and a declaration-based signal, which I am capable of writing; (b) descope E-02/E-03 out of the plan and approve the recording half; (c) mark the plan REJECT - NEEDS REPLAN | Option (a) is the tempting one and it exceeds a reviewer's authority in a way that matters: replacing a prose-scan proxy with a `- Carrier:`/`- Item-Dependencies:` signal changes WHAT THE RULE DETECTS, not just how, so it would be me deciding the product and then reviewing my own decision. Option (b) is a legitimate outcome but it is the maintainer's call, because it abandons the detection half the backlog item specifically asked for. Option (c) overstates it: the diagnosis, the recording half, and the refusal of option (b) are all sound and reusable, so "needs replan" would discard correct work. Escalation is the honest move, and the workflow's own guidance is explicit that a `Blocking: yes` question makes the lint gate refuse at every checkpoint, which I verified fires | yes |
| D-2 | PR-701: is the infeasibility really a blocker, or a performance nit to note? | BLOCKER | (a) Record it as a MEDIUM performance finding and let the rule ship, since `info` findings do not fail CI; (b) treat it as an implementation detail for the executor to optimize | Option (b) fails because the cost is inherent to the specified ALGORITHM (a filesystem walk per candidate token), not to a naive coding of it; I added an `lru_cache` and a 20-plan sample still did not finish in 18 minutes. Option (a) misreads what kind of defect this is: `AGENTS.md` states that a correct-but-slow path a human waits on qualifies as a bug, and gives the worked example of 128ms of a 530ms command being enough. Here it is minutes on a command run constantly. Shipping it would mean this bug-fix plan introduces a user-perceptible defect, which is worse than the silent gap it closes | no |
| D-3 | PR-702/PR-703: the baseline and the precedent are both wrong. Update the numbers, or change what is asserted? | UPDATE with the measured values AND restate the bar as a re-derived set comparison | (a) Just correct 32 to 51 and 0 to 1; (b) delete the baseline finding and require the executor to measure it fresh with no recorded expectation | Option (a) rots exactly as the original did, and faster here because the `plan-spec-link-missing` family alone moved 31 findings in days. Option (b) throws away the fact that MATTERS most, which is that the gate is currently RED, since an executor who does not know that will misread their own run. Recording the measured values as dated history while making the BAR "unchanged exit code and unchanged non-`info` SET, re-derived" keeps the signal without the rot, and is the same treatment the plan already applies correctly to its own suite baseline in F-10's second half | yes |
| D-4 | PR-704: OQ-02's deferral is spent. Resolve it, or leave it open beside the new OQ-03? | LEAVE IT OPEN, append a dated note, and let OQ-03 carry the decision | (a) Mark OQ-02 `resolved` and fold its content into OQ-03; (b) edit OQ-02's rationale in place to say the number is now known; (c) delete OQ-02 as superseded | Option (c) destroys the record of why the stop instruction existed, which is the most creditable thing about the plan's handling of this risk: the author anticipated exactly this failure and wrote the stop. Option (b) rewrites a question's reasoning to say something it did not say, which is the same class of record-rewriting D156 forbids for executed plans. Option (a) is close but marking it `resolved` would assert a resolution nobody made. Appending a dated note preserves the original judgement, records that its condition is met, and points at the question that now carries the decision | yes |
