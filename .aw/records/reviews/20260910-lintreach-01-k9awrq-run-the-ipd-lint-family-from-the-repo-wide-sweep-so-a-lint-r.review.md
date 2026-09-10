# Review: run the IPD lint family from the repo-wide sweep, child k9awrq (Set lintreach)

- Subject-Id: k9awrq
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `f3f87b90`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries no
`- Blocks-Release:`, correctly: backlog `q0h9ls` carries none.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE DEFECT IS REAL AND THE PLAN'S DIAGNOSIS IS RIGHT. I verified F-4 independently: `check_engine` calls
`ipd_lint.parse` in three places but never `lint_file`, so the whole `IPD-*` family is genuinely invisible to
the sweep. The `checkpoint=` versus `--phase` keyword trap is real and would have silently reported zero for
every file. The shared-evaluator precedent the plan wants to follow is real and is the right model. The
decision to decline a pre-commit hook as a substitute is correct and well reasoned.

THE PLAN'S CENTRAL PREMISE HAS BROKEN SINCE IT WAS WRITTEN, AND THAT IS THE REVIEW. Its whole shape rests on
"the author-phase corpus is clean, so introduce this BLOCKING on day one with no phased rollout". I re-ran
the measurement: 608 plans, and the author phase now yields 16 diagnostics across 10 files, all `IPD-Q501`,
each returning `disposition: error` so `aw ipd lint --phase author` already exits 1 on them. All 10 are
visible to a check-style sweep. A blocking introduction would fail CI on day one.

THE CAUSE EXONERATES THE AUTHOR AND SHARPENS THE FIX. `IPD-Q501`'s blocking-open-question form landed in
commit `ec865c2d` at 21:11 on 2026-09-08; this plan was committed at 10:16 the same day, and ancestry
confirms the rule came after. The measurement was honest when taken and was invalidated by a rule that did
not yet exist. Nor are the 10 files defects: they are legitimately `reviewed` plans carrying `Blocking: yes`
questions that are correctly waiting on the maintainer. There is nothing to triage.

AND THE RULE'S OWN COMMENT ALREADY FORBIDS WHAT THIS PLAN WOULD HAVE DONE. `check_open_questions` records the
maintainer's 2026-09-08 ruling that `IPD-Q501` was scoped to `Blocking: yes` precisely because the wider form
"would have declared the repository broken and would have forced an agent to edit other agents' in-flight
plans to get its own commit through". A blocking tree-wide sweep reproduces exactly that outcome by a
different route: my commit fails because ten other agents' plans await the maintainer's answers. So the plan
would have re-created a failure mode this repository had deliberately rejected nine hours before its premise
broke.

THE REPAIR IS ONE SEVERITY DECISION, NOT A REPLAN. Introduce the rule ADVISORY: the sweep gains reachability,
`aw check` reports what `aw ipd lint` would refuse, no agent is blocked on another's pending human decision,
and the backlog item's actual ask (that the tree-wide verdict SEE the family) is fully satisfied. I did not
resolve whether it should ever become blocking, because the corpus being clean at `author` is not a stable
property (the count returns to nonzero every time a reviewer correctly escalates a question), so escalation
is a workflow policy call about answer latency. That is OQ-04, non-blocking.

ONE TRAP IN THE REPAIR ITSELF, which I would have fallen into: "advisory" is not achieved by choosing the
word. `artifact_core.drift_exit_code` exempts only `info`, and this repository's own
`check.review-decision-unescalated` comment says in as many words that a `warning` DOES drive a nonzero
findings exit. Worse, an UNREGISTERED code falls back to `error` with an empty invariant, so omitting the
registration would silently give the strictest behavior. The plan now requires the exit code be measured, not
inferred.

Five findings, all FIXED in place, no deferrals. One new non-blocking open question. E-item and V-item counts
are unchanged at five each.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | BLOCKER | IN-SCOPE | D. anti-regression; A. correctness | re-measured 608 plans -> 16 `IPD-Q501` across 10 files, each `disposition: error`; `aw ipd lint --phase author` exits 1 on them; `_iter_type_files(repo,"plans")` -> 104 files, all 10 present; `ec865c2d` (21:11) vs `25f56bc2` (10:16) with ancestry confirmed; `check_open_questions`' scoping-ruling comment | **THE PLAN'S CENTRAL PREMISE HAS BROKEN, SO A BLOCKING INTRODUCTION WOULD FAIL CI ON DAY ONE.** The plan is built on a measured clean author-phase corpus and explicitly says no phased rollout is needed. The corpus is no longer clean, because `IPD-Q501` landed ELEVEN HOURS AFTER the plan was committed. The 10 offenders are healthy `reviewed` plans awaiting maintainer answers, not defects, so nothing is triageable; and a blocking rule would force one agent's commit to depend on another agent's pending human decision, which is verbatim the outcome the maintainer's `IPD-Q501` scoping ruling rejected | C:Low; U:High; S:Low; F:High; Overall:Medium | FIXED | Severity inverted to ADVISORY across Concern, Scope, E-01, E-02, E-05, under-scope, required tests and the gate; E-01 rewritten with the re-measurement, the cause, the offender list and an explicit no-edit/no-weaken instruction; OQ-03 re-resolved (its contingency has fired, so the fallback is now the plan); new Deferred entries forbid weakening `IPD-Q501` and defer blocking severity. New F-2 (superseded), F-11, F-12, F-13, and OQ-04 puts escalation to the maintainer |
| PR-902 | HIGH | IN-SCOPE | A. correctness; C. architecture | `artifact_core.drift_exit_code` exempts only `info`; `check.review-decision-unescalated`'s comment ("DO NOT READ `warning` AS 'cannot fail anything' ... a `warning` DOES drive a nonzero findings exit"); `_DEFAULT_RULESPEC` | **THE OBVIOUS FIX FOR PR-901 DOES NOT WORK BY ITSELF, so prescribing "advisory" without measuring would ship the very failure it was meant to avoid.** A `warning` severity still drives a nonzero findings exit here; only `info` is exempt. And an unregistered rule code falls back to `error` with an empty invariant, so forgetting the `RuleSpec` entry silently yields the strictest behavior. The plan's E-02 said to register a code but named no severity and required no exit-code measurement | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 requires the registration, names `warning` as the floor, and REQUIRES the exit code be measured unpiped before and after rather than inferred from the severity word; required-tests makes the unchanged exit code the primary no-regression criterion (replacing the now-unavailable zero-findings expectation); the fence forbids `error` and forbids leaving it unregistered. New F-14 |
| PR-903 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | measured bare `2 failed, 5957 passed, 3 skipped, 2 xfailed`; `test_orchestrator_retirement` -> `112 passed`; `test_runner_backlog_close.py` alone -> `47 passed`; `.gitignore:49` | **The suite baseline is wrong in both halves and the real failure invites destroying another party's work.** The plan cites `1 failed, 5648 passed` naming `test_orchestrator_retirement`, which passes. The real failures are the reporting-contract parity test, caused by the GITIGNORED `opencode-recovery/` tree of another party's session transcripts, and a load-sensitive SIGINT test that passes in isolation and fails on a 30-second timeout under `-n auto` | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 and required-tests carry the re-measured baseline with both node ids and the load-sensitivity note; the `opencode-recovery/` prohibition is in both the fence and required-tests; V-05 requires node-id comparison and confirmation the directory was untouched. New F-15 |
| PR-904 | MEDIUM | IN-SCOPE | E. testing; G. executability | E-05's "expected result is ZERO new findings"; the measured 16 findings | **E-05's success criterion is now unsatisfiable as written, and the tempting way to satisfy it is destructive.** With 16 `IPD-Q501` findings live, an executor told to expect zero has three options: edit ten other agents' plans (forbidden by the shared-checkout rule), filter or weaken `IPD-Q501` (which would leave the sweep reachable-but-silent, delivering the appearance of this plan's value with none of it and re-opening the gap the askme work closed), or report a failure. The plan named none of these | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05's expectation restated as "exactly the measured `IPD-Q501` population, and the exit code unchanged", with explicit prohibitions on fixing the plans and on weakening or filtering the rule; the `aw check all` per-rule requirement now says a ZERO count is itself a failure signal; a new Deferred entry names the suppression shortcut and why it is forbidden; V-05 requires the no-edit confirmation |
| PR-905 | LOW | IN-SCOPE | Evidence accuracy | corpus re-count: 608 tracked `.ipd.md` (item said 488, plan corrected to 561) | **The corpus figure has now been wrong twice in three days, which is an argument about method rather than arithmetic.** The plan correctly caught the item's stale 488 and wrote 561; the real figure at review is 608. A bare count with no measurement date will keep going stale in a repository adding plans daily | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-8 rewritten with the re-measured 608, the twice-moved history, the passing guard's own result (`66 passed`), and the note that a citation should carry its measurement date; E-01 and V-01 now compare against the REVIEW baseline rather than the authoring one |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The premise broke (PR-901). Reject as needing replan, or repair the severity in place? | REPAIR IN PLACE as an ADVISORY introduction. The plan's diagnosis, phase choice, wiring design, no-fork discipline and test structure are all correct and unaffected; only the severity conclusion depended on the broken measurement, and reachability alone satisfies the backlog item's stated ask | REJECT - NEEDS REPLAN (rejected: one severity decision changed, not the approach, and replanning would discard a sound diagnosis plus four sound E-items); keep it blocking and require the executor to wait for a clean corpus (rejected: the corpus is not reliably ever clean, since `IPD-Q501` fires whenever a reviewer correctly escalates and the maintainer has not yet answered, so this would strand the plan indefinitely) | 16 findings on 10 healthy plans; the item asks that CI and the sweep SEE the rule, which advisory delivers; `IPD-Q501` scoping-ruling comment | yes |
| D-2 | Should the new rule ever become blocking, and if so when? | ASK THE MAINTAINER via non-blocking OQ-04 with three routes costed. Did NOT decide it | Decide "yes, once the corpus is clean" (rejected: that condition is not stable, so it is not a decision but a deferral disguised as one); decide "never" (rejected: it is a legitimate policy position but it is the maintainer's to take, and blocking-on-a-subset is a real third option worth putting in front of them) | The count returns to nonzero on every correct escalation; the scoping ruling shows the maintainer has already weighed this exact trade | yes |
| D-3 | The 10 offending plans belong to other agents and their questions await the maintainer. Fix, report, or suppress? | REPORT ONLY, with explicit prohibitions on editing them AND on weakening or filtering `IPD-Q501`. Named the suppression shortcut in Deferred so it is refused rather than discovered | Fix the questions (rejected: they are the maintainer's decisions to make, and editing another agent's in-flight plan violates the shared-checkout rule); filter `IPD-Q501` out of the sweep (rejected, and this is the important one: it is the only rule currently firing, so filtering it would make the sweep reachable-but-silent and would re-open the gap the askme work had just closed) | The three sampled offenders are `- Status: reviewed`; `check_open_questions`' comment on being forced to edit others' plans | yes |
