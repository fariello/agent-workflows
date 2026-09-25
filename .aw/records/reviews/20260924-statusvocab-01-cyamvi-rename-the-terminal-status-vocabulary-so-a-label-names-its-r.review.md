# Review findings: plan cyamvi

- Subject-Id: cyamvi
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `166bf49b`. The plan file was committed and unchanged, so no pre-review snapshot was
needed. Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE
semantic review, so nothing below is structural; `--phase review-finalize` conforms after revision.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value therefore
rests on RUNNING the claims rather than re-reading them, which is what produced every finding below.

THE PLAN'S CENTRAL DIAGNOSIS IS CONFIRMED, and it is the strongest part of the plan. Re-measured on
`run-20260924T050407Z-3108751` (28 items, as claimed):

```text
lkexaw  partial                 7p3tt8  substantially-complete -> pending/    (0 of 5 items performed)
m7gvuz  failed-safely           xdvglg  substantially-complete -> executed/   (6 of 6 items performed)
m7gvuz  failed-safely      -> executed/  (refused itself; work landed unchanged)
```

One token described both `7p3tt8` (nothing performed, nothing landed) and `xdvglg` (everything
performed, landed), while the plan that behaved best in the run read `failed-safely`. The
anti-correlation F-01 asserts is real.

THE TWO SUPPORTING CODE CLAIMS ALSO HOLD:

```text
EXECUTION_SUCCESS_STATES        = {'substantially-complete', 'executed'}
runner_stop.STOPPED_DISPOSITION = 'interrupted'
'interrupted' in TERMINAL_STATES = False          # F-05: implemented but unregistered
artifact_audit:490  st = "complete" if status == "substantially-complete" else status
```

EIGHT FINDINGS, ALL FIXED IN PLACE. Three matter more than the rest: the plan named the wrong consumer
for its own harm claim (PR-002), declared seven spec paths that no longer exist (PR-001), and described
the `blocked` status in a way the code contradicts (PR-008, raised by the maintainer).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G (executability) | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` | ALL SEVEN declared spec paths in `- Scope-Paths:` are stale: the specs tree moved to status subdirectories (`approved/`, `to-review/`, `draft/`, `implementing/`) and every declared path points at the old flat location. The finalize scope gate reconciles declared against actual, so E-08 would edit seven undeclared files and refuse to finalize. Two of the seven are NOT `approved` (`z7nbn1` is `to-review`, `i4gpto` is `draft`), which the plan does not acknowledge. Spec `c4gd2h` is cited twice for R21 (E-04, V-04) and was undeclared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All seven paths corrected to their real subdirectory; `c4gd2h` added to `- Scope-Paths:`. |
| PR-002 | BLOCKER | IN-SCOPE | A (correctness) | `agent_workflows/runner_shared.py` `edge_satisfied` | THE HARM CLAIM NAMES A CONSUMER THAT NO LONGER READS THE SET. The Concern and F-06 both say `EXECUTION_SUCCESS_STATES` "is the DEPENDENCY BAR that `edge_satisfied` consults". Measured: `edge_satisfied` mentions it ONLY in a comment narrating the shortcut the maintainer REMOVED on 2026-09-19; its live `executed:` branch requires `plan_bucket(dep_path) == "executed"`. An executor following the plan would "fix" an already-correct branch. The set IS live, through `success_states=` into `decide_orchestrator_dispatch` (orchestrator retirement) and the cascade pass that marks a dependent `dependency-blocked`. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Concern re-pointed to the two real consumers, with an explicit warning not to edit `edge_satisfied`'s already-correct branch. |
| PR-003 | HIGH | IN-SCOPE | A (correctness) | `.aw/records/runs/run-20260924T050407Z-3108751/state.json` | F-02 claims `executed` matched `executed/` membership "exactly", with "no false positives and no false negatives". Re-measured over all 28 items: zero false positives but THREE FALSE NEGATIVES (`yeh7gc` `dependency-blocked`, `m7gvuz` `failed-safely`, `xdvglg` `substantially-complete` are all in `executed/` and all in `main`). The true claim is DIRECTIONAL, and the error matters because V-09 was written against the false version. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 rewritten as a directional claim with the three counter-examples named; noted that the asymmetry strengthens rather than weakens the plan's case. |
| PR-004 | HIGH | IN-SCOPE | E (verification) | plan `V-09` | V-09 required the `Landed` column to agree with `executed/` membership "for every item", and called a disagreement "a failure of this item". Against the PR-003 measurement that bar is unsatisfiable-as-written and, worse, would ACCEPT a wrong column: a `Landed` reading `no` for the three landed-but-not-`executed` items would pass a naive status-versus-landed equality check. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-09 restated as a DIRECTIONAL bar: `Landed` must agree with the DIRECTORY, must not be required to agree with the STATUS, and status-versus-landed disagreements are expected output. |
| PR-005 | MEDIUM | IN-SCOPE | G (live-artifact criteria) | plan `E-07` | E-07 pins ten per-token census counts as the surface its guard must cover. Five had ALREADY DRIFTED two days later, before any work started (`substantially-complete` 79 tests not 81; `blocked` 88/115 not 83/112; `integration-blocked` 10 not 9; `merge-refused` 41 not 40). This is the live-artifact-count violation the IPD rubric names, and the plan's own conventions section forbids the same pattern for line offsets. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Counts relabelled CONTEXT with a re-derive-at-execution requirement and the measured drift quoted; V-07 aligned so a delta is expected rather than a failure. |
| PR-006 | HIGH | IN-SCOPE | A (correctness) | `agent_workflows/artifact_audit.py` | E-06 describes ONE `"complete"` coercion site. There are FOUR, plus TWO module-level tables encoding the same conflation (`_TERMINAL_EXPECTED_DIR` maps `"complete" -> "executed"`; `_RUN_SUCCESS_STATUSES` is `frozenset({"executed", "complete"})`). Fixing only the quoted site is exactly the partial landing E-07 exists to catch. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now names all four sites and both tables and requires enumeration by symbol before editing; V-06 requires all six shown removed or justified as a legacy read. |
| PR-007 | MEDIUM | UNDER-SCOPE | E (verification) | `.aw/records/plans/pending/` | E-05 states the DIRECTION of its behavior risk but never measures the blast radius, and V-05 asks the executor for a count the plan could have supplied. Measured at review: six `executed:` edges across all pending plans, six distinct targets, ALL SIX already in `executed/`, so narrowing the bar changes no dispatch decision today. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measurement added to E-05 as the argument for landing it now, with an explicit re-derive requirement since the population is live. |
| PR-008 | HIGH | IN-SCOPE | A (correctness) | `agent_workflows/runner_shared.py` `_VERDICT_TABLE`, and the four pre-flight refusal arms | THE PLAN'S DESCRIPTION OF `blocked` IS FALSIFIED BY THE CODE (raised by the maintainer, who asked why `fail-gate` fits a status the plan itself described as the agent quitting). OQ-01 asserted `blocked` "means the agent stopped and preserved its work". THE AGENT NEVER SETS IT. Measured over all 209 `blocked` items in `.aw/records/runs/`: 179 `clean_base_refusal`, 9 `begin_refusal`, 5 `worktree_error`, 16 from the verifier's `VERDICT_BLOCKED`/`VERDICT_NOT_CONFORMING` arms. Four of five producers are PRE-FLIGHT GATES that refuse before an agent session starts, each recording its reason; the fifth is the VERIFIER, a different authority, and E-03's original wording would have mapped it to `fail-gate`. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | OQ-01 resolved on the measurement (`fail-gate` correct on evidence, `failed` rejected because the reason IS recorded); E-03 now splits the legacy token, verifier arms to `fail-verify` and pre-flight arms to `fail-gate`, with the read-alias asymmetry stated in the map's comment. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-02: does collapsing the four `merge-*` tokens to one `fail-merge` change retry behavior, as the plan assumes without verifying? | No: collapse is safe. Recorded in OQ-02 as resolved, with E-02/V-02 still required to paste the evidence. | Leaving it as an unverified assumption for the executor (rejected: it gates whether the collapse is safe at all, and the check is cheap); keeping four tokens (rejected: no evidence they are read). | `runner_shared.reattempt_deferred_integrations` contains NO `integration-blocked` or `merge-conflict` literal and selects work from the durable `preserved_*` deferral record, so the retry decision cannot key on the status token. | yes |
| D-2 | Should `c4gd2h` be added to `- Scope-Paths:` when the plan cites it twice but declares no edit to it? | Added it, since E-04/V-04 rest on its R21 and an amendment may prove necessary; declaring it is cheap and an undeclared spec edit refuses at finalize. | Leaving it undeclared (rejected: if E-04 needs even a clarifying sentence the run refuses at finalize, which is the failure PR-001 already found seven times). | Managed-block rule in `AGENTS.md`: every `.spec.md` a plan will touch must be listed in `- Scope-Paths:`; the runners announce declared spec edits before a run starts. | yes |

### Round 1 verdict

APPROVE WITH REVISIONS APPLIED. Eight findings, all FIXED in place, none deferred and none left open.
OQ-02 resolved from code evidence (D-1). OQ-01 resolved from a 209-item measurement after the maintainer
challenged the plan's premise (PR-008); both open questions are `Blocking: no` and both are now answered.
No unfixed BLOCKER or HIGH remains, so readiness is `go-pending-approval`.

ONE ITEM THE MAINTAINER SHOULD APPROVE EXPLICITLY, as the plan's own gate already asks: E-05 narrows
`EXECUTION_SUCCESS_STATES` to `{executed}`. PR-007 measures its blast radius as ZERO today, which is the
best possible moment to land it, but it is still the one behavior change in an otherwise-rename plan.

ONE DEFECT FOUND AND DELIBERATELY NOT FIXED HERE, recorded so it is not lost: the 16 verifier-sourced
`blocked` items leave NO reason field on the item, unlike all four pre-flight gates which record one.
That is a missing-record defect, not a vocabulary defect, and this plan renames outcomes rather than
adding records. It needs its own plan.

## Round 2

Opened at the maintainer's direction after they challenged round 1's PR-008 fix: if the label is meant
to name the authority that refused, why do `aw ipd begin` refusing and a lane failing to allocate both
land on `fail-gate`? They were right, and round 1 under-split. `- Status:` was `reviewed` and NOT yet
`approved`, so amending the plan is legitimate rather than a post-approval edit.

ROUND 1 WAS INCOMPLETE, NOT WRONG. It corrected the plan's false claim that the agent sets `blocked`,
and split the verifier arms out to `fail-verify`. What it missed is that the four remaining producers
answer to THREE authorities, so `fail-gate` still bundled unrelated causes:

```text
209 'blocked' items across all run records in .aw/records/runs/
  179  clean_base_refusal   -> fail-gate    read next: git status in the driver's checkout
    9  begin_refusal        -> fail-begin   read next: the plan's open questions / Scope-Paths
    5  worktree_error       -> fail-lane    read next: git branch --list 'aw/lane/*'
   16  (verifier verdict)   -> fail-verify  read next: the verifier's own output
```

The `begin_refusal` texts are specific and actionable (`IPD-S404 OQ-03: unresolved blocking question at
pre-execution`; `refusing to begin: uncommitted changes to paths INSIDE this plan's Scope-Paths`), and
all five `worktree_error` texts are one recurring cause:

```text
git worktree add failed for lane '8zgybk': fatal: a branch named 'aw/lane/8zgybk' already exists
```

WHAT "MY TREE" MEANS, since the maintainer asked and round 1 left it vague. The dirty-base guard runs
`git status --porcelain --untracked-files=no` against the DRIVER's repo path, BEFORE any lane exists
(`evaluate_clean_base_for_launch` precedes both `allocate_isolation_worktree` call sites in
`execute_item_core`), so the tree measured is the MAIN CHECKOUT and never a lane. Untracked files never
refuse. And the consequence splits on isolation, per `lane_containment.evaluate_clean_base`'s
`shared_tree` flag: a dirty ISOLATED base is reported and PROCEEDS, a dirty SHARED tree REFUSES. So the
179 refusals are shared-tree runs (`--no-isolate-worktree`) meeting uncommitted tracked changes in the
main checkout.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-009 | HIGH | IN-SCOPE | F (KISS / naming) | `agent_workflows/runner_shared.py` `execute_item_core` refusal arms; `.aw/records/runs/*/state.json` | ROUND 1's `fail-gate` STILL BUNDLED THREE AUTHORITIES, breaking the plan's own rule that a label names whose output to read next. Measured over 209 `blocked` items: the dirty-base gate (179), `aw ipd begin` declining authority (9), and lane allocation failing (5) send an operator to three different places, so one label cannot serve them. Ten labels was therefore one too few by two. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `fail-begin` and `fail-lane`; vocabulary target is now TWELVE. E-03 carries a per-producer table with counts and a READ NEXT per label; E-01's canonical set updated; V-03 now requires each of the four producers driven and its token pasted, since a test asserting only "no legacy token" would pass with all four collapsed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-3 | Should `worktree_error` map to `fail-lane` or to the generic `failed`? | `fail-lane`. | `failed` (rejected on evidence): defensible because the site is an `except Exception` and so is mechanically a crash rather than a deliberate refusal. | All five measured occurrences carry ONE named, recurring, fixable cause (`fatal: a branch named 'aw/lane/<id6>' already exists`), so the cause is diagnosed, not unknown. This plan reserves `failed` for "broken in a way none of the above covers"; filing a known cause there is how `substantially-complete` became meaningless, which is the defect this plan exists to remove. Maintainer concurred 2026-09-24. | yes |
| D-4 | The legacy `blocked` token now splits four ways on WRITE. What should a legacy READ map to? | `fail-gate`, single-valued. | Per-producer reconstruction (rejected): a historical run record carries the reason FIELD but the alias map is keyed on the status token alone, so the map cannot see it; a reader wanting the finer answer already has `clean_base_refusal` / `begin_refusal` / `worktree_error` on the item. | `fail-gate` is the 179-of-209 majority, so a legacy read is right 86% of the time and never claims the work landed. E-02's requirement is that a legacy token classify identically to its replacement for TERMINALITY, which holds for all four. | yes |

### Round 2 verdict

APPROVE WITH REVISIONS APPLIED. One finding (PR-009), FIXED. Two decisions recorded (D-3, D-4), both
reversible. Round 1's eight findings remain FIXED and are not reopened. Readiness stays
`go-pending-approval`; the plan is still awaiting the human approval its own gate asks for, and E-05
(the one behavior change) still warrants explicit separate sign-off.

The missing-reason defect for the 16 verifier cases is unchanged and still needs its own plan: the four
pre-flight producers each record a reason on the item, the verifier arms record none, so `fail-verify`
names an authority whose output the item does not point to.
