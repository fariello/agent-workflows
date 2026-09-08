- Id: q0h9ls
- Status: graduated
- Set: lintreach
- Priority: medium
- Work-Kind: bug
- Summary: aw check plans does not run ipd_lint, so IPD-M107 (and every other lint rule) is invisible to the repo-wide sweep and to CI: a fabricated Readiness is caught only by 'aw ipd lint' or 'aw ipd begin'

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan k9awrq (lintreach-01). Core defect REPRODUCED not trusted: a scaffolded plan with a fabricated Readiness and no review yields IPD-M107 from aw ipd lint --phase author and ZERO findings from aw check plans --agent. TWO OF THE THREE OPEN DECISIONS ARE NOW SETTLED BY MEASUREMENT, which turned this from an exploration into a narrow plan. Question 1 demanded the noise count first: measured ZERO author-phase diagnostics across all 561 tracked plans, so the feared pre-existing backlog does not exist and the rule can be introduced blocking with no phased rollout. Question 2 asked which checkpoint: measured 1261 diagnostics across 74 files at pre-transition, ALL IPD-S404 (the correct state of an unexecuted plan), which forces 'author' and quantifies the alternative. Question 3 (a hook instead) is DECLINED using the item's own reasoning that a local hook is feedback not authority, not cloned, and skippable, so it cannot make CI see the rule; it stays a legitimate later addition. STALE: the closing note cites 488 plans in the corpus guard; the corpus is 561. That guard is deliberately left in place. KEYWORD TRAP recorded: the API keyword is checkpoint=, the CLI flag is --phase, and a wrong-keyword call inside a broad except reports zero for every file (the first measurement attempt returned 561 exceptions counted as zeros). No Blocks-Release on the item, so none inherited.
- 2026-09-06 created (aw backlog): aw check plans does not run ipd_lint, so IPD-M107 (and every other lint rule) is invisible to the repo-wide sweep and to CI: a fabricated Readiness is caught only by 'aw ipd lint' or 'aw ipd begin'

GRADUATED 2026-09-08 to plan `k9awrq` (`lintreach-01`). NOTHING IN THE CORE DEFECT IS OBSOLETE and it was
REPRODUCED rather than trusted: a scaffolded plan carrying a fabricated `- Readiness: go-pending-approval`
with no review in its history yields `IPD-M107` from `aw ipd lint --phase author` and ZERO findings from
`aw check plans --agent`.

TWO OF THE THREE OPEN DECISIONS ARE NOW SETTLED BY MEASUREMENT, which is what turned this from an
exploration into a narrow plan. QUESTION 1 asked for the noise count BEFORE choosing, warning that a
tree-wide lint "may surface a large pre-existing backlog". MEASURED across all 561 tracked plans by calling
`ipd_lint.lint_file(path, checkpoint="author")`: ZERO diagnostics across ZERO files. The feared backlog does
not exist, so the rule can be introduced BLOCKING on day one with no phased rollout and nothing to triage.
QUESTION 2 asked which checkpoint. MEASURED at `pre-transition` on the same corpus: 1261 diagnostics across
74 files, ALL `IPD-S404` ("E-01: not 'performed' at pre-transition"), which is simply the correct state of
every plan that has not executed. So `author` is the only defensible phase, and the cost of the alternative
is now quantified rather than feared.

QUESTION 3 (a pre-commit hook instead of the checker) is DECLINED with a reason rather than left open, using
this item's own framing: a local hook "is feedback, not authority", is not cloned by default, and is
skippable with `--no-verify`, so it cannot deliver what this item actually asks for, which is that CI and the
tree-wide verdict SEE the rule. A hook remains a legitimate ADDITION on top of a correct checker; it is not a
substitute.

ONE MEASUREMENT IN THE CLOSING NOTE IS STALE: it cites the corpus guard as "scanning all 488 plans"; the
corpus is now 561. The guard still passes and still covers one rule. It is deliberately LEFT IN PLACE by the
plan (deleting a passing corpus test while adding a checker is how coverage silently narrows).

A KEYWORD TRAP WORTH RECORDING, hit while measuring: the API keyword is `checkpoint=`, while the CLI flag is
`--phase`. A call using `phase=` raises, and inside a broad `except` it reports zero for every file, which is
indistinguishable from success. The first measurement attempt returned 561 exceptions counted as zeros.

Found 2026-09-06 while adding `IPD-M107` (the unattested-`Readiness` rule, Set `rdattest`).

MEASURED. With a fabricated `- Readiness: go-pending-approval` present in a tracked pending plan:

    $ aw ipd lint <plan> --phase author     -> error, IPD-M107 (caught)
    $ aw ipd begin <id6> --actor ...         -> refused, IPD-M107 (caught, blocking)
    $ aw check plans                         -> NO IPD-M107 finding at all

`check_engine` has its own targeted plan rules (`check_ipd_draft_ready`, `check_ipd_dependencies`,
naming, lifecycle transitions) but does NOT invoke `ipd_lint.lint_file`, so the entire `IPD-*`
diagnostic family is unreachable from the repo-wide sweep. Consequence: a defect that `aw ipd lint`
would refuse can be COMMITTED and will sit in the tree until someone lints that specific file or
tries to execute it.

WHY IT MATTERS BEYOND THIS ONE RULE: `aw check` is what an agent and CI are pointed at for a
tree-wide verdict, and `aw attention --check` is the fail-closed gate. A rule that only fires on a
per-file verb is a rule that only fires when someone already suspects that file.

WHAT TO DECIDE (not prescribed):
1. Should `aw check plans` run `ipd_lint` per plan, or a named SUBSET of its rules? Running the whole
   lint tree-wide may surface a large pre-existing backlog (the tree currently reports 45 `aw check`
   errors already), so this could be noisy. Measure the count BEFORE choosing, and consider a phased
   introduction (advisory first, blocking later) rather than a flag day.
2. Which checkpoint would a tree-wide sweep use? `author` is the only phase valid for an arbitrary
   pending plan; `pre-transition` would mass-fail every unexecuted plan, which is why the phase must
   be chosen deliberately rather than defaulted.
3. Is the right fix instead a pre-commit hook on STAGED plans (cheap, local, catches it at the moment
   of authoring), with `aw check` left alone? The repo already has this shape for several gates
   (`ipd-executed-gate`, `ipd-status-untooled-gate`), and it matches the honest limit that a local
   hook is feedback, not authority.

Note the corpus guard added with `IPD-M107`
(`tests/test_ipd_lint.py::ReadinessAttestationTests::test_every_readiness_carrying_plan_in_the_tree_is_attested`)
closes the gap for THIS ONE RULE by scanning all 488 plans in the suite. That is a deliberate
stopgap, not a general answer: it does not generalize to other `IPD-*` rules and it lives in the test
suite rather than in the checker.
