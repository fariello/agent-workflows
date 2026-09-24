# Review findings: plan kjqqzf

- Subject-Id: kjqqzf
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `06dd74cc` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review, so nothing found below is structural;
`--phase review-finalize` conforms after revision. `aw check` was also run: it reported
`check.ipd-uncarried-obligation` at `error` severity for this plan (F-10/PR-006), now cleared.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims rather than re-reading them, which is what produced the retraction below.

THE PLAN'S CENTRAL DIAGNOSIS IS FALSE, AND EVERY LOAD-BEARING CLAIM WAS MEASURED RATHER THAN REASONED.
The plan asserts that a cached model verdict in the orchestrator coverage probe "passed" two retirements
that ticked unperformed items. Three independent measurements refute it:

```text
# PR-001 (a): the probe is not on the retirement path at all
grep -c 'enforce_orchestrator_probe_gate(' across agent_workflows/*.py -> 1 definition, 1 call site
  (runner_shared.py, the PRE-QUEUE run gate)
inspect.getsource(ipd_lifecycle.retire_orchestrator):
  'probe'      in src -> False
  'coverage'   in src -> False
  'uncovered'  in src -> False
  'enforce_orchestrator' in src -> False
```

```text
# PR-001 (b): the decisive counterexample. A cached FAIL that retired anyway.
5e4sb6 digest 1667136bb82c...
  read_probe_verdict(model='uri/its_direct/pt3-claude-opus-5-1m-us')
  -> ProbeVerdict(verdict='fail', recorded_at='2026-09-22T02:37:19+00:00', stale_reason='')
5e4sb6 location -> .aw/records/plans/executed/  (retired 2026-09-24, run run-20260924T010059Z-999731)
```

A `fail` cannot both block and retire. The cached verdict permits the RUN to start; retirement is decided
by `evaluate_set_retirement` plus `retire_orchestrator`, which never consult it.

```text
# PR-001 (c): E-02's proposed "structural precondition" ALREADY SHIPS.
# Synthetic Set: orchestrator + one executed child + one APPROVED coverage child.
evaluate_set_retirement(tmp, 'covset')
  eligible = False
  reason   = unfinished-children
  detail   = Set 'covset' has 1 child(ren) that are not 'executed': cov111 (approved)

# Live, on the one census orchestrator still pending:
evaluate_set_retirement('.', 'hostdedup')
  eligible = False | reason = unfinished-children
  detail   = Set 'hostdedup' has 3 child(ren) that are not 'executed':
             nmlx47 (superseded), xdvglg (approved), 04vf1h (approved)

# And a cross-Set coverage child is refused by a different, also-shipped condition:
  reason = unauthored-child-rows
  detail = the orchestrator's child table declares row(s) '02' that resolve to no plan
```

SO THE RETIREMENTS WERE LEGITIMATE, AND THE HONEST RESULT IS THAT NO DEFECT OCCURRED IN THE GATE (PR-002).
Re-measuring the `wtd5m2` census found it staler than the plan said, in the direction that undermines the
plan: SIX of seven have now retired, not two, and every one of them had its coverage child execute WITH ITS
OWN ITEMS PERFORMED before the parent retired.

```text
parent   coverage child   child E performed   parent retired   child landed
y9s4vm   yv4tb1           4/4 E, 4/4 V pass   5fea858f 06:46   522fa084 06:43  (3 min earlier)
lyo1tz   1f7xno           7/7 E                0823163b 06:14   f821f71d 05:02
wfjsp4   ingpvc           4/4 E                06dd74cc         4170c5d0
tb63qv   k311gw           3/3 E                51a9a93b         b383a3f6
ao1rb7   2s0iym           4/4 E                d6677caf         dd64d590
5e4sb6   i3d6ml/tx6q0h/ct4w0a  all executed    444eec31
a5wdne   04vf1h (approved, NOT executed)  ->  retirement REFUSED, correctly
```

`6h7y2y` is `graduated` and `cnwy8g` is `done`, the two states the retired parents' E-03 items asked about.
No work was lost. F-2 (the terminal file's FORM contradicts its own commit) and F-6 survive; F-1, F-3 and
F-5 are retracted in place with their evidence.

THE REAL HOLE IS ONE THE PLAN NEVER MENTIONED (PR-004). `IPD-S407` already enforces exactly the typed
child-tracking row this plan wanted to invent, and it is blind to a plan at the moment retirement decides:

```text
_ORCH_ROW_BLOCKING_CHECKPOINTS = frozenset(('review-finalize', 'pre-transition'))
lint_text: a plan in a TERMINAL directory short-circuits to `legacy/not evaluated`
           for every checkpoint except `post-transition` (_is_terminal_dir)

              author        review-finalize  pre-transition  post-transition
y9s4vm   legacy/0 diags  legacy/0 diags   legacy/0 diags  conforming/0
lyo1tz   legacy/0 diags  legacy/0 diags   legacy/0 diags  conforming/0

# yet called DIRECTLY, the same rule condemns every row of both:
orchestrator_row_conformance(y9s4vm) -> applies=True conforming=False
  E-01/E-02/E-03 all reason='not-a-typed-child-tracking-row'
orchestrator_row_conformance(lyo1tz) -> applies=True conforming=False  (3 refusals)
# contrast a5wdne, authored after the rule: conforming=True, all four rows typed
#   '- [ ] E-01 CONFIRM li44r9 REACHED executed'  child_id6='li44r9' status='executed'
```

That is a genuine, measured gap with real consequence: the rule that would have forced these parents'
items into covered, typed rows audits nothing about them, and the contradiction F-2 reports is therefore
invisible to every tool.

TWO SMALLER MEASURED FINDINGS, both of which would have cost the executor a round trip:

```text
# PR-005: spec 77tr3o R-12(3) asserts a fact the tree contradicts
"ipd_lint.py must continue to contain zero occurrences of 'orchestrator'"
grep -c -i orchestrator agent_workflows/ipd_lint.py -> 47
# deliberately: r07vma landed IPD-S407 there, and
# tests/...::TheRejectedShapeWasNotTaken documents DELETING the word-count pin
# and replacing it with a behavioral Kind-parity assertion.

# PR-003: this plan collides with its own Set
read_set_membership('.', 'orchretire')
  orch: 84j8d7
  child order=1 id6=5942n7 status=executed
  child order=1 id6=kjqqzf status=to-review     <-- duplicate Order 1
evaluate_set_retirement('.', 'orchretire')
  -> unfinished-children: kjqqzf (to-review)
# so a Set that completed in September is now held open by this new plan.

# PR-006: the plan would block its own finalize
evaluate_durable_carrier -> severity=error,
  "8 obligation(s) name no durable carrier"
aw ipd lint --phase pre-transition -> 13 findings (12x IPD-S404 + the carrier rule)
# After revision: evaluate_durable_carrier -> 0 findings.
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G (plan executability); A (correctness) | `runner_shared.enforce_orchestrator_probe_gate` (one call site); `inspect.getsource(ipd_lifecycle.retire_orchestrator)`; `runner_shared.evaluate_set_retirement` | The plan's central causal claim is FALSE. The probe gate does not gate retirement (one caller, the pre-queue run gate; zero probe tokens in `retire_orchestrator`), proven by `5e4sb6` retiring 2026-09-24 with a cached `fail`. And E-02's proposed structural precondition already ships: `evaluate_set_retirement` refuses `unfinished-children` for an unexecuted coverage child, verified synthetically and live on `hostdedup`. Executing E-02 as written would have added a duplicate predicate for no behavior change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Title, Concern, Scope, Scope-Paths, E-01, E-02, findings F-1/F-3/F-5 and OQ-01 all rewritten in place. F-1/F-3/F-5 marked RETRACTED with their refuting evidence rather than deleted, so the plan records what it got wrong. |
| PR-002 | HIGH | IN-SCOPE | D (anti-regression); G | each parent's directory and `Execution state:` counts; each coverage child's performed-item count; `git log --diff-filter=A` landing times for `yv4tb1`/`y9s4vm` | The plan asserts a defect where measurement shows correct behavior, and its `wtd5m2` census is staler than it claims (6 of 7 retired, not 2). Every retired parent's coverage child executed WITH its own items performed before the parent retired (`yv4tb1` 4/4 E + 4/4 V, landing 3 minutes before `y9s4vm`). Left uncorrected, an executor would "fix" a working gate. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-4 re-measured and downgraded to INFO with the full six-parent table; F-6 kept; E-01 rewritten to demand the causation answer and the relative landing times, and to state explicitly that a report merely re-asserting the Concern has not performed the item. |
| PR-003 | MEDIUM | IN-SCOPE | C (architecture/operability) | `runner_shared.read_set_membership`; `evaluate_set_retirement` | The plan's own `- Set: orchretire` / `- Order: 1` duplicates executed plan `5942n7`. Measured: two Order-1 children, and `evaluate_set_retirement('orchretire')` now refuses on `kjqqzf`, holding a completed historical Set open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-9, raised as OQ-04 (resolved from convention, remedy named: regroup with `aw group plans`/`aw rename plans`), and made an explicit precondition in the gate so it cannot be skipped. Not renamed here: this workflow reviews and revises a plan, and renaming the artifact under review is an authoring act for the executor. |
| PR-004 | HIGH | UNDER-SCOPE | E (testing/verification); G | `ipd_lint._ORCH_ROW_BLOCKING_CHECKPOINTS`; `ipd_lint._is_terminal_dir` in `lint_text`; `orchestrator_row_conformance` | The shipped rule that already expresses what this plan wants (`IPD-S407`, typed child-tracking rows) is BLIND at the moment retirement is decided: it fires only at `review-finalize`/`pre-transition`, and a plan in a terminal directory short-circuits to `legacy/not evaluated` at both. `y9s4vm`/`lyo1tz` return 0 diagnostics while the rule called directly condemns all three rows of each. The plan never mentions `IPD-S407`, `r07vma`, or the short-circuit. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added as F-7 and made E-02's new target, with both candidate ends named, the safer one recommended, and the Kind-parity property (`TheRejectedShapeWasNotTaken`) pinned as a must-stay-green constraint. `ipd_lint.py` added to `- Scope-Paths:`; `runner_shared.py` removed. |
| PR-005 | MEDIUM | IN-SCOPE | F (honest documentation) | spec `77tr3o` R-12(3); `grep -c -i orchestrator agent_workflows/ipd_lint.py` -> 47; `TheRejectedShapeWasNotTaken` docstring | The spec asserts `ipd_lint.py` must contain zero occurrences of "orchestrator". It contains 47, deliberately. An executor reading R-12(3) literally would conclude E-02 may not touch `ipd_lint.py` at all, which is the opposite of the correct conclusion. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-8; E-02 now states the surviving constraint is the BEHAVIORAL Kind-parity one and requires amending R-12(3)'s stale sentence in the same change, with the `.spec.md` declared in `- Scope-Paths:` first. |
| PR-006 | MEDIUM | IN-SCOPE | G (plan executability) | `check_engine.evaluate_durable_carrier` -> `error`, "8 obligation(s) name no durable carrier"; `CARRIER_CUTOVER_DATE = 20260919` | The plan is post-cutover and carried eight obligations with no durable carrier, so `aw check plans` reports `error` and `aw ipd lint --phase pre-transition` merges the same finding. The plan would have blocked its own finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every `## Deferred` row and every open question now carries `- Carrier:` or `- Carrier-Declined:`. Re-measured: `evaluate_durable_carrier` -> 0 findings. Recorded as F-10 and as a gate precondition. |
| PR-007 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's `## Approval and execution gate`; `ipd_lifecycle.finalize` vs `retire_orchestrator` | The gate lacked the conditional lifecycle-transition ownership (runner vs executor), lacked a scope fence as a DECLARATION with the `--scope-reason`/`--scope-ack` reconciliation, and its V-items demanded evidence aimed at the retracted diagnosis (V-02 asked for a refusal the shipped code already produces, which would have passed trivially). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten with the declaration-style scope fence, the conditional finalize ownership, one genuine stop condition (E-01's measurement contradicting this review), and the two preconditions. All four V-items rewritten to demand evidence for the re-aimed items, including a fail-first demonstration and a no-live-corpus inspection. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is this plan REPLAN (its premise is false) or repairable with bounded edits? | Repair in place: retract the false findings with evidence, re-aim E-02 at the measured hole (F-7), keep E-03/E-04 which survive. | REPLAN and retire the plan as `not-executed`: rejected because two of its findings (F-2 the record-form contradiction, and F-6) are real and unowned by any other artifact, and a genuine new hole (F-7) was found in the same area, so a replacement plan would have substantially the same shape. Retiring it would also strand its inherited `Blocks-Release: next`. | `AGENTS.md` (retire only when there is no bounded repair); F-2 verified by `lint_file` returning 0 diagnostics at `pre-transition` for both terminal plans; F-7 verified by `orchestrator_row_conformance` condemning all six rows | yes |
| D-2 | Which end should E-02 fix: the rollup consulting row-conformance, or the terminal short-circuit stopping its suppression of `IPD-S407`? | Do not decide for the executor; name both, recommend the rollup end, and require the choice be recorded with its reason. | Mandating the short-circuit change: rejected because `_is_terminal_dir` grandfathers EVERY terminal plan in the tree (43 in `executed/` per the in-module note) and changing it could redden a large corpus of historical plans, which is a far wider blast radius than the retirement path. | `ipd_lint._is_terminal_dir` / `_with_name_check`'s grandfathering comment; measured that all four census parents lint `legacy/not evaluated` pre-transition | yes |
| D-3 | Should this review rename/regroup the plan to fix the `orchretire` Order-1 collision (F-9/PR-003)? | No. Record it, name the tooling remedy, and make it a gate precondition for the executor. | Renaming it here with `aw rename plans`: rejected because `/plan-review` reviews and revises plan CONTENT, and renaming the artifact changes its identity and its Set's membership, which is an authoring act; doing it mid-review would also invalidate the lane input path the driver tracks. | `plan-review.md` Step 2.4 (surgical edits to the plan), Step 4 (commit only reviewed plan files); `AGENTS.md` "do not hand-name plans" | yes |
| D-4 | The plan is `Blocks-Release: next` inherited from a `bug` backlog item, but PR-001/PR-002 show no bug occurred in the gate. Should the release gate be cleared? | Leave `Blocks-Release: next` in place. | Clearing it with `--blocks-release -`: rejected because F-2 and F-7 are real, and F-7 in particular is a live blind spot in a safety mechanism; the gate is therefore still earned even though the originally-claimed defect was not. Also, the gate belongs to backlog `wtd5m2` and re-deciding a release gate is a maintainer scope call. | `AGENTS.md` release-gates section ("every live bug gates the next release"; the gate travels with the work); F-7 measured this review | yes |
| D-5 | OQ-01 through OQ-03 were `open`. Resolve them from evidence, or leave them open and report NO-GO? | Resolve all three from measured evidence and add OQ-04 resolved, recording the basis in each rationale. | Leaving them open: rejected because the repository answered every one. OQ-01's branches both rested on the falsified premise; OQ-02's constraints are fixed by `rollup_history_message` already emitting the honest sentence plus the no-ticking rule; OQ-03's premise (that the retirements were defective) is refuted by the coverage-child evidence. Asking the human what the tree already answers is forbidden by the workflow's memory kernel. | `plan-review.md` Step 3.1 ("Resolve questions from authoritative evidence first. Do not ask the human what the repository already answers") | yes |

### Deferred and open

None. Every finding is FIXED. No finding is DEFERRED, OPEN, or REPLAN, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule.

### Notes on what was NOT changed, and why

- `evaluate_set_retirement` and `retire_orchestrator` were NOT proposed for a new precondition. PR-001
  establishes the precondition already exists; adding a second is the re-fork discipline this repository
  spends plans preventing.
- The two terminal plan files (`y9s4vm`, `lyo1tz`) were NOT edited. `AGENTS.md` forbids adding commits to
  a plan in `executed/`, and F-4 establishes their retirements were correct, so there is nothing to
  correct beyond the WRITER, which E-03 owns.
- No code, test, or spec file was touched by this review. Only the plan under review and this record.
