# Review findings: plan zngiya

- Subject-Id: zngiya
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed the ORCHESTRATOR of Set `statusvocab` (Order 00). Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize` conforms after the revisions, so nothing below is structural. The plan file
was committed and unchanged, so no pre-review snapshot was needed.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
MEASURING the claims against the tree rather than re-reading them, which is what produced all three
findings.

SCOPE OF THIS REVIEW, stated because it decides what is and is not a finding here. This is an
ORCHESTRATOR: it holds three child-confirmation rows and contributes no code, no test, and no record.
So the review asks orchestrator questions - is the sequencing right, are the declared dependencies
real, is every deliverable owned by exactly one child, and does the gate carry an execution contract -
and does NOT re-review the children's own content. Order 01 (`cyamvi`) already carries two rounds and
reads `reviewed` / `go-pending-approval`; Orders 02 and 03 are `to-review` and need their own reviews
before the Set can execute end to end.

THE ORCHESTRATION IS SOUND AND THE STRUCTURE IS RIGHT, which is the main finding and the reason this
is a revisions-applied pass rather than a replan. Verified independently:

```text
Kind: orchestrator            (own first `- Kind:` bullet, not a containment scan)
Highest E allocated: 03       3 E-items, 3 V-items, 1:1 bijection
every E row                   `E-NN CONFIRM <child-id6> REACHED executed`  -> IPD-S407 typed rows
child table                   3 rows, ids cyamvi / 787hb4 / 9x7otz, all resolve to real files
E-03 Depends on: E-01         mirrors `9x7otz`'s own `- Item-Dependencies: executed:cyamvi`
```

The parent carries NO work of its own, so the ORCHESTRATOR COVERAGE GATE should pass it by
construction: each of the three deliverables (the vocabulary, the send-back, the `Landed` column plus
spec amendments) is owned by exactly one named child.

THE SEQUENCING CLAIM CHECKS OUT AGAINST THE CHILDREN'S OWN FRONT MATTER. Order 03 declares
`executed:cyamvi` and the parent's E-03 declares `Depends on: E-01`, so the two agree. Order 02
declares `- Item-Dependencies: none` and genuinely touches neither the vocabulary nor a gate
(`- Scope-Paths:` is `runner_shared.py`, `ipd_lifecycle.py` and three test files), so F-03's claim that
it could ship alone is true. Dependency depth will also order this correctly without the declaration,
since `queue_sort_key` ranks depth first and treats every non-orchestrator Set member as a prerequisite
of its orchestrator.

THREE FINDINGS, ALL FIXED IN PLACE. One is a correctness claim the Set's own child review had already
corrected and this parent reintroduced in looser wording; one is a provenance misattribution that would
send an executor to the wrong plan; one is a materially incomplete gate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G (executability) | `.aw/records/plans/pending/20260924-statusvocab-00-zngiya-make-a-run-status-name-its-refusing-authority-and-make-an-an.ipd.md` `## Approval and execution gate` | THE GATE CARRIED ALMOST NO EXECUTION CONTRACT: two sentences (human approval, plus the dependency-bar caveat) and nothing else. Missing were the scope fence, the paste-the-actual-output honesty rule, the path-scoped-commit-and-never-push rule, the lifecycle transition, and the disposition of OQ-01. The omission is worse than usual on an ORCHESTRATOR: retirement is performed by `runner_shared.dispatch_orchestrator_item` -> `ipd_lifecycle.retire_orchestrator` on a disk-state verdict and deliberately SKIPS the pre-transition E/V checkpoint, so V-01..V-03 can be marked complete having never been inspected, and an executor reading this gate was told nothing about which path owns the transition. Two sibling orchestrators in `pending/` (`d0cbt3`, `a5wdne`) both carry the full contract including that retirement warning, so the shape was available and simply not applied. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten to carry: `Size assessment: standard`; OQ-01 dispositioned as non-blocking and explicitly not to be re-decided mid-run; a DECLARATION-style scope fence (make-then-justify with `--scope-reason`/`--scope-ack`, no stop-over-scope, with the genuinely-unsafe exception preserved); the hard-MUST honesty rule; path-scoped commit through `aw commit` plus the shared-checkout `git diff --cached` check and never-push; the CONDITIONAL lifecycle transition (runner retires it with no agent turn, do NOT run `aw ipd finalize` under a runner, no hand-rolled `git mv`, executor owns it only on the by-hand path); a note that Order 03 is the only child that may amend a spec; and an explicit statement that retirement skips the checkpoint, with why that is tolerable here. |
| PR-002 | MEDIUM | IN-SCOPE | A (correctness) | `agent_workflows/runner_shared.py` `edge_satisfied`, `decide_orchestrator_dispatch` | THE CONCERN REINTRODUCED THE IMPRECISION ORDER 01'S ROUND 1 HAD ALREADY CORRECTED. It read "the vocabulary's worst token is a member of the live dependency bar", which is the same loose framing `cyamvi` PR-002 was raised against. Measured: `edge_satisfied` reads `EXECUTION_SUCCESS_STATES` only in a COMMENT narrating the in-run shortcut the maintainer REMOVED on 2026-09-19; its live `executed:` branch calls `resolve_plan_path` then requires `plan_bucket(dep_path) == "executed"`, i.e. the DIRECTORY. The real consumers are `decide_orchestrator_dispatch` (passed `success_states=EXECUTION_SUCCESS_STATES` by each host) and the drain/cascade labeling. An executor who reads the parent for context and the child for detail would arrive at the child already believing the wrong consumer, which is precisely the wasted edit the child's round 1 spent a BLOCKER preventing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern now names both real consumers BY SYMBOL and states explicitly that `edge_satisfied` is NOT one, with the reason (its branch already reads the directory), so the correction survives in the parent as well as the child. |
| PR-003 | MEDIUM | IN-SCOPE | G (executability) | `git log -S "IPD-S407" -- agent_workflows/`; commit `70678847` | PROVENANCE MISATTRIBUTION. The conventions section credited `IPD-S407` to "`orchtyped` Order 04 `68uhp0`". The rule code and its single validation function were landed by Order 01 `dpdyed`: commit `70678847` "feat(ipd_lint): land the typed child-tracking row grammar and its one shared validation function (IPD-S407)", whose body states "Implements approved spec r07vma R1a/R3/R7/R8 as Order 01 of Set orchtyped" and "No consumer is wired here by design". `68uhp0` is Order 04 and MIGRATED the then-pending orchestrators onto the row (its `- Scope-Paths:` is `.aw/records/plans/pending`, `ipd_lint.py`, one test). An executor tracing the invariant to its source would read the migration plan rather than the grammar, and the migration plan does not define the rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Attribution corrected to `dpdyed` (Order 01) for the grammar and `ipd_lint.orchestrator_row_conformance`, with `68uhp0`'s actual migration role named separately. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The run directory `.aw/records/runs/run-20260924T050407Z-3108751`, which every measurement in this plan and its children rests on, does not exist in this lane. Does that make the plan's evidence unverifiable, and is it a finding? | NOT a finding. Treat the measurements as verified-by-proxy and do not re-raise the missing directory. | (a) Raise a BLOCKER that the central evidence is unavailable. (b) Re-measure from the run directory in the main checkout. Rejected: the lane is the complete authorized workspace and climbing out is forbidden; and `.aw/records/runs/` is gitignored, so no clone has it. | `.aw/records/runs/` is absent from this whole worktree, not merely from the lane, and is gitignored by construction, so its absence is expected rather than a defect. The claims it supports were independently corroborated: all five cited plans resolve on disk with the stated dispositions (`xdvglg`, `7p3tt8`, `m7gvuz`, `04vf1h` all in `executed/`, `a5wdne` still in `pending/`), `7p3tt8`'s finalize commit `0a0e6b73` exists, and the code-side claims verify directly (`EXECUTION_SUCCESS_STATES == {"executed", "substantially-complete"}`, `runner_stop.STOPPED_DISPOSITION == "interrupted"`, `"interrupted" not in TERMINAL_STATES`). Order 01's own round-1 record also quotes the per-item measurement taken when the directory was readable. | yes |
| D-2 | Should this review re-review the two children that are still `to-review` (`787hb4`, `9x7otz`), or restrict itself to the orchestrator that was named? | Restrict to the named orchestrator; read the children only as evidence for the parent's sequencing and ownership claims. | Reviewing all four plans in one pass. Rejected: it would put three plans in the ledger that were never candidates. | `plan-review` Step 0.1: the ledger contains ONLY plans explicitly named in the invocation plus any a documented eligibility rule adds; a file referenced only as evidence is not in scope. No repository rule adds a Set's children to a review of its parent. | yes |
| D-3 | The parent's `- Scope-Paths:` declares only its own file. Is that under-declaration, given the Set touches 17 modules and 8 specs? | Correct as declared; not a finding. | Declaring the union of the children's paths. Rejected: it would make the finalize scope gate demand a `--scope-ack` for every path this plan legitimately never touches. | The plan contributes no code, test, or record of its own, and each child declares its own paths. The finalize scope gate reconciles declared against ACTUAL per item, so a parent declaring paths it does not edit would refuse rather than pass. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author        --agent zngiya  -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent zngiya -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)

TERMINAL_STATES                     13 tokens (10 run outcomes + executed/approved/reviewed)
EXECUTION_SUCCESS_STATES            {"executed", "substantially-complete"}
runner_stop.STOPPED_DISPOSITION     "interrupted"
"interrupted" in TERMINAL_STATES    False        (the promotion Order 01 E-01 performs)
legacy tokens Order 01 renames      10, and all 10 are in TERMINAL_STATES; the 3 unrenamed
                                    members are exactly approved/executed/reviewed, which the
                                    Set correctly excludes (it does not touch the review family)

child files                         all 3 resolve in pending/ with matching Order and Id
9x7otz `- Item-Dependencies:`       executed:cyamvi        (agrees with parent E-03)
787hb4 `- Item-Dependencies:`       none                   (agrees with F-03's ship-alone claim)
cyamvi `- Status:`                  reviewed, Readiness go-pending-approval
787hb4 / 9x7otz `- Status:`         to-review              (each still needs its own review)
```

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001..PR-003 all FIXED, none deferred, none open. OQ-01 remains open
and is `Blocking: no` with a recorded recommendation, which under the 2026-09-10 maintainer ruling does
not make the plan `NO-GO`.

Readiness `go-pending-approval`. Two things a human should know before approving, neither of which is a
finding against this file: Order 01's narrowing of `EXECUTION_SUCCESS_STATES` to `{executed}` is a
behavior change the gate now asks to be approved explicitly (blast radius measured at ZERO today, six
`executed:` edges across `pending/` all naming targets already in `executed/`), and Orders 02 and 03
are still `to-review`, so the SET cannot execute end to end until they are reviewed and approved even
though this orchestrator is cleared.
