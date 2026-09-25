# IPD: Make aw commit and aw work begin block only on error-severity plan findings, so a warning rule cannot silently acquire commit-blocking authority

- Date: 2026-09-24
- Kind: child
- Concern: `work_cmd._validate_plan_via_engine`, which backs BOTH `aw work begin` and `aw commit`, keeps every plan finding whose severity is not exactly `info`, so any rule registered `warning` silently acquires commit-blocking and begin-blocking authority the moment it fires on a plan, contradicting every `warning` RuleSpec comment in `check_engine` that says the tier adds no lifecycle gate and must not block a commit.
  THE DEFECT IS LIVE AND ORDINARY, NOT LATENT, AND THE PLAN'S OWN F-2 UNDERSTATED IT BY MEASURING TOO EARLY (corrected at review as F-7). At the review HEAD `de94e2dc` THREE `warning` rules reach this gate, not one: `check.review-decision-unescalated` plus `check.ipd-priority-required` and `check.ipd-work-kind-required`, which landed in `9e3ed86e` (a DESCENDANT of the authoring HEAD `877545fc`) and fire on ANY plan whose `- Status:` is `approved`/`auto-approved` and which lacks either field. Measured end to end: such a plan gets `aw commit: refusing - 2 finding(s)` and `aw work begin: refusing to start - 2 finding(s)` naming both rules, while the same plan carrying `- Priority:`/`- Work-Kind:` commits normally. So an operator today can be refused a commit by a rule whose own registry comment stages it as advisory. Note the two are DELIBERATELY staged toward `error` (F-8), which this plan records rather than reverses.
- Scope: IN: change the gate predicate in `work_cmd` so only `error`-class findings (including the conservative `_DEFAULT_RULESPEC` `error` for an unregistered rule, and any unrecognized severity string, which fails closed) refuse; print `warning` findings as a named, non-blocking advisory on both verbs instead of dropping them; keep `info` silent as today; record in a `work_cmd` code comment that two of the reaching `warning` rules are deliberately STAGED toward `error` and will block here once promoted (E-07, from F-8); add a new test module covering warning-commits-with-advisory and error-still-refuses for both verbs, with a fixture that carries `- Priority:`/`- Work-Kind:` and an asserted finding-free baseline; one CHANGELOG line. OUT: `artifact_core.drift_exit_code` and the `aw check` exit-code contract (a different contract where `warning` deliberately fails CI); re-tiering any rule's severity; removing the plan-findings gate altogether (OQ-02); rewording `check_engine` comments that describe the exit-code contract.
- Scope-Paths: agent_workflows/work_cmd.py, tests/test_work_gate_severity.py, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: gatesev
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: s7cu7n
- From-Backlog: 7a53rm
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history
- 2026-09-25 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED; F-2's narrowing conclusion corrected (three warning rules reach the gate, not one; the two omitted landed after the authoring HEAD), E-03/E-04 fixture corrected, E-07/V-07 added for the lkexaw staged-severity interaction, OQ-03 added and resolved (D-2); readiness GO - PENDING HUMAN APPROVAL

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 7a53rm; re-measured at HEAD 877545fc that a registered `warning` finding located at the plan makes `aw commit` exit 1 with "refusing", and that of the nine `warning` rules only `check.review-decision-unescalated` is actually reachable from the gate's `check_type(repo_root, "plans")` call today (the other eight run only in the `check_types` full sweep).

## Goal

Make the plan-findings gate in `aw commit` and `aw work begin` honor the three-tier severity model the rest of the engine documents: `error` refuses, `warning` is printed as a visible advisory that does not refuse, `info` stays silent. This removes the trap where registering a deliberately advisory `warning` rule silently changes what `aw commit` refuses (measured by `k9awrq` when `check.ipd-lint` at `warning` broke four commit/begin tests).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the defect before changing it

- [ ] E-01 RE-MEASURE the defect at the executing HEAD before editing. Run a throwaway probe (under `/tmp`, not committed) that builds a tmp git repo with one conformant pending plan (`- Scope-Paths: src/`), patches `agent_workflows.check_engine.check_type` to return one `artifact_core.Drift(str(plan), "check.review-decision-unescalated", "probe")`, and drives `cli.main(["commit", "<id6>", "--dir", <root>, "-m", "m", "--", "src/f.py"])`. At authoring this printed `aw commit: refusing - 1 finding(s) on ...: check.review-decision-unescalated: probe` with rc 1. Repeat with `check.name-nonconformant` (error) to show the same refusal. Also confirm `check_engine.rule_spec("check.review-decision-unescalated").severity == "warning"`. If the warning case already commits, STOP: the defect is fixed and this plan should be retired, not executed.
  ALSO RE-DERIVE THE REACHABLE-WARNING SET RATHER THAN TRUSTING F-2's AUTHORED LIST, which was measured before `9e3ed86e` landed and is now WRONG (see F-7). Do NOT re-run the spy over `check_*` callables and conclude from it: it is what missed the two rules, because they reach the gate through `check_content`'s plans branch rather than through a separately-named sweep function. Instead measure the ONE thing the gate actually consumes, with an UNPATCHED engine: build the fixture and print every `(severity, rule)` that `check_engine.check_type(root, "plans")` returns for the plan path, enriched. Record the list in V-01. Then, for each `warning` rule in it, state whether the E-02 fix is the intended outcome for that rule or whether it needs a maintainer decision (see OQ-03), and STOP and report if the list contains a `warning` rule this plan has not considered.
  - Depends on: none
  - Expected outcome: pasted probe output showing a `warning` finding refuses `aw commit` (rc 1) at the executing HEAD, the error case also refusing, AND the re-derived enriched `check_type(root, "plans")` list for the fixture plan with every `warning` rule in it named.
  - Execution state: pending

### Task group 2: fix the predicate

- [ ] E-02 In `agent_workflows/work_cmd.py`, change `_validate_plan_via_engine` to PARTITION the plan's enriched findings instead of filtering only `info`: return `(blocking, advisory)` where `advisory` holds findings whose severity is exactly `warning`, `info` findings are dropped as today, and `blocking` holds EVERYTHING ELSE (so `error`, an unregistered rule that `check_engine.enrich_drift` stamps with `_DEFAULT_RULESPEC`'s `error`, an empty severity, and any unrecognized severity string all refuse: the gate fails closed on anything it does not positively recognize as advisory). Update both call sites, `run_work_begin` and `run_commit`: refuse (rc 1, unchanged "refusing" message and per-finding lines) only on a non-empty `blocking`; when `advisory` is non-empty, print one header line naming the count, the plan, and that it is not blocking (e.g. `aw commit: note - 1 advisory (warning) finding(s) on <plan> (not blocking):`, and the `aw work begin:` equivalent), followed by `  <rule>: <detail>` per finding, BEFORE proceeding. Print advisories even when also refusing, so the operator sees the full set. Update the function docstring, the `# Validate BEFORE mutating` comment in `run_work_begin`, and the module docstring bullet `(fail closed on findings)` to say "fail closed on error-severity findings; warnings are printed as advisories". Do NOT touch `artifact_core.drift_exit_code`.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/work_cmd.py` shows the partition, both call sites updated, docstrings aligned; no other module changed.
  - Execution state: pending

- [ ] E-07 RECORD THE STAGED-SEVERITY INTERACTION IN THE `work_cmd` CODE COMMENT, so the next reader of this gate is not misled about what `warning` promises here. This is a COMMENT-ONLY item in a file already in `- Scope-Paths:`; it changes no behavior and must not re-tier any rule. Two `warning` rules reaching this gate (`check.ipd-priority-required`, `check.ipd-work-kind-required`) are DELIBERATELY STAGED, and executed plan `lkexaw` E-04 records that the end state is `error`: "`warning` while the pending corpus still carries sentinels, `error` once it does not. Note the end state is `error`; nothing may leave the rule permanently at `warning`". So E-02 does NOT permanently exempt them; when they are promoted to `error` they will block this gate again, BY DESIGN, and that is the correct outcome rather than a regression this plan must prevent (OQ-03). Beside the new partition, state: that `warning` here means "not blocking at THIS lifecycle gate", that it is NOT a claim about the `aw check` exit code (`artifact_core.drift_exit_code` exempts only `info`, so a `warning` still fails CI), and that a rule staged at `warning` en route to `error` will block here once promoted, naming `lkexaw` as the precedent. Do not restate the exit-code contract anywhere else and do not edit `check_engine.py`.
  - Depends on: E-02
  - Expected outcome: `git diff agent_workflows/work_cmd.py` shows a comment naming the two staged rules, the `lkexaw` end-state obligation, and the two-contracts distinction; `git diff --stat` still lists only the three Scope-Paths files.
  - Execution state: pending

### Task group 3: tests

- [ ] E-03 CREATE `tests/test_work_gate_severity.py` (the former `tests/test_work_primitives.py`, which encoded the begin/commit behavior, was deleted by commit `19313eed` "test: trim test suite", so there is no existing test to edit). Build a tmp git repo fixture modelled on the deleted module's `WorkPrimitivesTest.setUp` (retrievable with `git show 19313eed^:tests/test_work_primitives.py`): a conformant approved plan `20260828-wk-01-wk0001-demo.ipd.md` with `- Scope-Paths: src/, tests/`, `.gitignore` for `.aw/worktrees/` and `.aw/state/`, an initial commit. If the tests exercise `aw work begin`, declare the execution role via `tests.support.declare_execution_role` or `coordinator_role` as the other lifecycle tests do, so an ambient worker marking cannot change the outcome. `aw commit` cases: (a) a patched `check_engine.check_type` returning one `check.review-decision-unescalated` Drift at the plan path: rc 0, output contains `advisory` and the rule id, and `git show --stat HEAD` contains the committed path; (b) the same with `check.name-nonconformant`: rc 1, output contains `refusing` and the rule id, HEAD unchanged; (c) an UNREGISTERED rule id (e.g. `check.gatesev-probe-unregistered`): rc 1, proving fail-closed on the default `error`; (d) one warning plus one error: rc 1, and the output names BOTH rules.
  THE FIXTURE PLAN MUST CARRY `- Priority:` AND `- Work-Kind:`, which the deleted module's `_PLAN` does NOT, and this is measured rather than cautionary. That fixture is `- Status: approved` with neither field, so `check_plan_priority_required` (landed by `9e3ed86e`, AFTER this plan was authored) fires TWO real `warning` findings on it: measured at review, the deleted fixture unpatched gives `aw commit: refusing - 2 finding(s) ... check.ipd-priority-required ... check.ipd-work-kind-required` and `aw work begin: refusing to start - 2 finding(s)` with the same pair. COPYING IT VERBATIM WOULD MAKE EVERY CASE MEASURE THE WRONG THING: case (a) would pass for the wrong reason after the fix (two extra advisories it does not assert on), and case (b)/(c)/(d) would refuse over rules they never named, so a reverted-predicate mutation run could not discriminate. Add both fields with real vocabulary values (for example `- Priority: medium`, `- Work-Kind: chore`), and ASSERT the clean baseline explicitly: one case must show the UNPATCHED fixture produces NO `warning` or `error` finding at the plan path (print the enriched `check_type(root, "plans")` list), so a future rule that starts firing on the fixture fails loudly here instead of silently corrupting every other case.
  - Depends on: E-02
  - Expected outcome: the new module's `aw commit` cases pass against the fix, case (a) FAILS when the E-02 predicate is reverted to the `== "info"` skip, and the baseline case shows the unpatched fixture is finding-free at `warning` and above.
  - Execution state: pending

- [ ] E-04 In the same module, add `aw work begin` cases: (a) the `warning` Drift: rc 0, output contains `allocated worktree` and `advisory`, and `.aw/state/work/wk0001/work-lease.json` exists; (b) the `error` Drift: rc 1, output contains `refusing to start`, and NO lease file exists; (c) one UNPATCHED end-to-end error case mirroring the deleted `test_work_begin_fails_closed_on_findings`: a second plan named `badname.ipd.md` with `- Id: bad001` genuinely trips `check.name-nonconformant`, and `aw work begin bad001` refuses with rc 1 and no lease. Case (c) guards against the patching seam diverging from the real engine.
  CASE (c) MUST ASSERT ON THE RULE ID, NOT MERELY ON rc 1, and must give the second plan the two fields too. Measured at review with the deleted fixture's shape: `aw work begin bad001` refuses with THREE findings (`check.name-nonconformant` plus the two `ipd-*-required` warnings), so an rc-only assertion passes even if `check.name-nonconformant` stopped firing entirely, which defeats the purpose of having an unpatched case. Assert that the output contains `check.name-nonconformant` AND that no `warning`-tier rule id appears in it, which after the fix is the correct combined statement: the error refused, and no warning contributed to the refusal.
  - Depends on: E-02
  - Expected outcome: the `aw work begin` cases pass against the fix, and case (a) FAILS with the predicate reverted.
  - Execution state: pending

### Task group 4: user-facing record and suite

- [ ] E-05 Add one `- Fixed:` bullet to the pending `## 2.0.0 (pending)` section of `CHANGELOG.md` stating that `aw commit` and `aw work begin` no longer refuse over a warning-level finding on the plan; they print it as a non-blocking note and still refuse over errors. Plain prose, no em or en dashes (user-facing, per the execution contract).
  - Depends on: E-02
  - Expected outcome: one new CHANGELOG bullet, no dashes of the forbidden kinds.
  - Execution state: pending

- [ ] E-06 Run the BARE suite `python3 -m pytest` (no extra flags) after E-02..E-05.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the bare suite summary line shows no failures attributable to this change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SEVERITY IS THREE TIERS AND THE ENGINE SAYS SO REPEATEDLY. `check_engine.RULE_REGISTRY` entries for `warning` rules state the tier "adds no LIFECYCLE gate (no `aw ipd lint` checkpoint, no begin/finalize refusal, no dependency block)" (`check.review-decision-unescalated`), "must not block a commit or set an exit code" (`check.review-dangling`), and "should be visible without blocking a commit" (`check.graduated-to-repeated`). `check_engine.check_review_dangling`'s docstring repeats "NO LIFECYCLE GATE consumes it". The `work_cmd` predicate is the outlier.
- TWO DIFFERENT CONTRACTS SHARE THE WORD "GATE". `artifact_core.drift_exit_code` ("only error/warning-class findings drive the nonzero exit") governs the EXIT CODE of `aw check` and CI, and `warning` failing there is deliberate (the `check.system-layout-*` comment: "`warning` states the condition truthfully without weakening the gate"). The `work_cmd` gate is a LIFECYCLE action gate. This plan changes only the latter; conflating them is how `k9awrq` F-14 reached the false conclusion the backlog item cites.
- AN UNREGISTERED RULE DEFAULTS TO `error`. `check_engine.rule_spec` falls back to `_DEFAULT_RULESPEC = RuleSpec("error", ...)` and `enrich_drift` stamps it, so an error-only predicate is still fail-closed for a new rule an author forgets to register.
- THE PLAN-GATE REACH IS `check_type(repo_root, "plans")`, NOT THE FULL SWEEP. Cross-tree rules (setid length, name identity, review-dangling, release gates, system layout, graduated-to) run only in `check_engine.check_types`; see F-2.
- BUT `check_content`'s PLANS BRANCH IS PART OF THAT REACH, AND IT IS WHERE PLAN-SCOPED RULES ACCUMULATE. `check_type(repo_root, "plans")` reaches `check_content`, whose plans branch calls `check_ipd_dependencies`, `check_plan_priority`, `check_plan_work_kind`, `check_plan_priority_required`, `check_ipd_draft_ready`, `check_review_finding_unescalated` and `check_review_decision_unescalated`, each with the recorded rationale "the concern is plans-scoped ... reached by BOTH `aw check plans` and the `aw check all` fan-out, exactly once". So enumerating gate-reachable rules by spying on separately-named `check_*` sweep functions MISSES this whole family, which is exactly how F-2 missed the two rules F-7 names. Measure the reachable set by calling `check_type(root, "plans")` on a real fixture and enriching the result; do not infer it from call-site greps.
- A `warning` MAY BE A STAGED ROLLOUT TOWARD `error`, NOT A PERMANENT TIER. `lkexaw` E-04 states the pattern and the obligation: "`warning` while the pending corpus still carries sentinels, `error` once it does not. Note the end state is `error`; nothing may leave the rule permanently at `warning`". A gate that stops blocking on `warning` must therefore not be described as permanently exempting such a rule.
- COMMITS go through `aw commit <plan> -- <paths>`; tests run bare as `python3 -m pytest`; when a narrowed run needs per-test counts use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All re-measured at HEAD `877545fc` (`git rev-parse --short HEAD`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `work_cmd._validate_plan_via_engine` | CONFIRMED. The gate drops only `info`; a `warning` finding at the plan path refuses `aw commit` exactly like an `error`. | Code: `if enriched.severity == "info": continue  # advisory nudge, not a blocking finding`. Probe (patched `check_type`, real `cli.main(["commit", ...])`): `check.review-decision-unescalated warning rc= 1 \| ['aw commit: refusing - 1 finding(s) on 20260828-wk-01-wk0001-demo.ipd.md:', '  check.review-decision-unescalated: probe']`; `check.name-nonconformant error rc= 1` identical shape. Direct: `check.setid-length-warn warning blocks= True`, `check.ipd-draft-ready-to-review info blocks= False`. |
| F-2 | MED (SUPERSEDED BY F-7 AT REVIEW; its narrowing conclusion is now WRONG, its sweep-seam mechanics remain correct) | `check_engine.check_type` vs `check_engine.check_types` | THE "NINE WARNING RULES BLOCK COMMITS TODAY" FRAMING IS OVERSTATED. `python3 -c "... [v.severity, k] for RULE_REGISTRY if severity != 'error'"` lists nine `warning` rules (graduated-to-repeated, identity-absent-from-name, orphaned-live-blocker, review-dangling, review-decision-unescalated, setid-length-warn, stale-index-stale, system-layout-drift, system-layout-missing). But the gate calls `check_type(repo_root, "plans")`, and a spy over every `check_*` callable showed only `check_review_decision_unescalated` is reached; `check_setid_length`, `check_review_dangling`, `check_release_gates`, `release_gate_warnings`, `check_system_layout`, `check_name_identity` are `NOT reached` (they run in `check_types`' full-sweep seam). `check.stale-index-stale` is emitted by `plans_index.check_drift`, which `check_content` calls only when `include_retired` is true, and the gate does not pass it. So today exactly ONE warning rule can block, and only when its finding is located at the plan (the irreversible-unescalated branch; the malformed-review and missing-`Reversible` branches locate at the review path and are filtered out). The DEFECT is still real because it is a latent trap for any future plan-scoped `warning` rule, which is precisely what `k9awrq` hit. | spy probe output quoted; `check_engine.check_types` comments "rides this once-per-full-sweep seam"; `check_review_decision_unescalated` emits `_core.Drift(str(plan_path), _REVIEW_DECISION_RULE, ...)` only for the unescalated-irreversible branch |
| F-3 | INFO | `check_engine.RULE_REGISTRY` | NO `warning` rule was registered in order to block commits. Every `warning` RuleSpec comment that addresses commits says the opposite (see Step 0). The one rule deliberately chosen to be non-`info` for a real obligation (`check.review-decision-unescalated`) justifies that choice by EXIT CODE, not by a commit gate. So no rule needs to be raised to `error` as part of this fix. | quotes in Step 0; `grep -n "block.\{0,20\}commit" agent_workflows/check_engine.py` hits: "it must not block a commit or set an exit code", "should be visible without blocking a commit" |
| F-4 | INFO | `tests/test_work_primitives.py` | THE TEST FILE THE BACKLOG ITEM NAMES NO LONGER EXISTS. It was deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 896 lines removed). No remaining test drives `run_commit`'s or `run_work_begin`'s findings gate (`grep -rn "run_work_begin\|_validate_plan_via_engine" tests/` is empty). So nothing encodes the old behavior and nothing currently guards the new one; E-03/E-04 create the coverage. | `git show 19313eed --stat \| grep work_prim` -> `tests/test_work_primitives.py \| 896 -----` |
| F-5 | INFO | `check_engine.check_content` comment | A comment beside `check_review_decision_unescalated` says "Advisory (`warning`), so it never sets an exit code", which is false for the exit code (`drift_exit_code` exempts only `info`) and was the other source of confusion. Not this plan's contract; recorded in Deferred. | quoted comment text in `check_content`'s plans branch |
| F-6 | INFO | `8dto0g` (executed) | The original design intent is "fail closed on any blocking finding" with "advisory info-severity nudges excluded"; it never defined `warning` as blocking, it just predates the third tier being used for plan-scoped rules. Fail-closed is preserved by making the blocking set "everything not positively advisory". | `8dto0g` E-01 execution note: "filtered to the plan (advisory info-severity nudges excluded) and fails closed on any blocking finding" |
| F-7 | HIGH | `check_engine.check_plan_priority_required`, reached from `check_content`'s plans branch | ADDED AT REVIEW (finding PR-001). F-2's CONCLUSION IS WRONG AT THE EXECUTING HEAD AND UNDERSTATES THE BLAST RADIUS BY AN ORDER OF MAGNITUDE. Two `warning` rules F-2 never enumerated, `check.ipd-priority-required` and `check.ipd-work-kind-required`, ARE plan-scoped, DO emit at the plan path, and DO refuse both verbs today. They are absent from F-2's nine-rule list because they did not exist when it was measured: they landed in `9e3ed86e` (planprio `lkexaw`), which is a DESCENDANT of the authoring HEAD `877545fc`. So the count of gate-reachable `warning` rules is THREE, not one, and unlike `check.review-decision-unescalated` (which needs an irreversible unescalated review decision to exist) these two fire on ANY plan whose `- Status:` is `approved`/`auto-approved` and which lacks either field, i.e. the ordinary case this gate meets. F-2's SPY METHOD is what missed them and must not be reused: they reach the gate through `check_content`'s plans branch rather than a separately-named sweep function. | at review HEAD `de94e2dc`: `git show 877545fc:agent_workflows/check_engine.py \| grep -c ipd-priority-required` -> `0`; `git merge-base --is-ancestor 877545fc 9e3ed86e` -> true; enriched `check_type(root, "plans")` on a fresh `approved` fixture without the fields -> `warning check.ipd-priority-required`, `warning check.ipd-work-kind-required`, `info check.ipd-lint-diagnostic`; end to end `aw commit` -> `refusing - 2 finding(s)` naming both, and `aw work begin` -> `refusing to start - 2 finding(s)` naming both; the same fixture WITH `- Priority: high`/`- Work-Kind: chore` -> `aw commit: committed 1 path(s)`; registry sweep shows ELEVEN `warning` rules, not nine, the two extra being exactly these |
| F-8 | MED | `lkexaw` E-04 (executed) | THE TWO RULES F-7 NAMES ARE DELIBERATELY STAGED, WITH A RECORDED END STATE OF `error`, which changes what this plan may claim. `lkexaw` E-04 says verbatim: "`warning` while the pending corpus still carries sentinels, `error` once it does not. Note the end state is `error`; nothing may leave the rule permanently at `warning`". So E-02 does not permanently exempt them, and it MUST NOT be described as doing so; when they are promoted they will block this gate again, by design. This does NOT weaken the fix (the two rules are enforced independently and more strictly by `aw ipd lint`/`aw ipd begin`, measured: the same fieldless approved plan yields `IPD-M110`/`IPD-M111` at both `author` and `pre-execution`, and `aw ipd begin` refuses with "no receipt written"), but it does oblige the plan to record the interaction rather than silently assume `warning` is permanent. E-07 records it in the code; OQ-03 records the decision. | `lkexaw` E-04 quoted; measured at review: `aw ipd lint --phase author` and `--phase pre-execution` on a fieldless `approved` plan both rc 1 with `IPD-M110`/`IPD-M111`; `aw ipd begin` rc 1 "pre-execution gate did NOT conform (error); no receipt written" |
| F-9 | LOW | plan `V-05` as authored | THE PROPOSED DASH CHECK CANNOT PRINT `0` THE WAY V-05 EXPECTS, AND ITS EXIT CODE IS MISLEADING. `grep -c` on no match prints `0` but EXITS 1, so under any `set -e` or `&&` chain the evidence step reads as a failure of the check rather than as a pass, and an executor may "fix" it by changing the expectation. Measured: `printf 'a - b\n' \| grep -c $'\u2014\|\u2013'` prints `0` and exits 1; with a real em dash it prints `1` and exits 0. | measured at review; also `grep -c $'\u2014\|\u2013' CHANGELOG.md` -> `0` today, so the file is already clean and the new bullet is the only thing at risk |

## Proposed changes (ordered, validatable)

1. E-01 re-measures that a `warning` finding refuses `aw commit` at the executing HEAD, AND re-derives the gate-reachable `warning` set from an unpatched `check_type(root, "plans")` rather than from F-2's stale list (STOP if already fixed, or if an unconsidered `warning` rule appears).
2. E-02 partitions findings in `work_cmd._validate_plan_via_engine` into blocking (everything not `warning`/`info`) and advisory (`warning`), and makes both verbs refuse only on blocking while printing advisories.
3. E-07 records in a `work_cmd` comment that two reaching `warning` rules are staged toward `error` (`lkexaw`) and will block here once promoted, and that this gate's tier meaning is not a claim about the `aw check` exit code.
4. E-03 adds `aw commit` tests on a fixture carrying `- Priority:`/`- Work-Kind:` with an asserted finding-free baseline: warning commits and prints the advisory; error, unregistered rule, and mixed warning+error refuse.
5. E-04 adds `aw work begin` tests: warning allocates and prints the advisory; patched error and a real misnamed plan refuse with no lease, asserting on the rule id rather than on rc alone.
6. E-05 records the behavior change in `CHANGELOG.md`.
7. E-06 runs the bare suite.

## Deferred / out of scope (with reason)

- CHANGING `artifact_core.drift_exit_code` OR THE `aw check` EXIT CONTRACT. `warning` failing a CI exit is deliberate and documented (`check.system-layout-*` RuleSpec comment); only the lifecycle action gate is wrong.
  - Carrier-Declined: Intended behavior of a different contract, not an outstanding obligation.
- REMOVING THE PLAN-FINDINGS GATE FROM `aw commit`/`aw work begin` ENTIRELY (the backlog's question 2). Resolved as OQ-02 default: keep it for `error` findings.
  - Carrier-Declined: Resolved in OQ-02 on repository evidence; revisiting is a maintainer choice with no open obligation.
- CORRECTING THE FALSE "so it never sets an exit code" COMMENT in `check_engine.check_content` (F-5). It is a comment about the exit-code contract in a file outside this plan's scope; a one-line comment fix is cheap but widening scope into `check_engine.py` for it invites contention with the many plans that touch that file.
  - Carrier-Declined: Cosmetic comment inaccuracy about a different contract; the RuleSpec comments beside it already state the correct behavior ("DO NOT READ `warning` AS 'cannot fail anything'"), so no reader is misled without also seeing the correction.
- RE-TIERING ANY RULE. F-3 found no `warning` rule that relies on blocking commits, so none is raised to `error`. AMENDED AT REVIEW: F-7/F-8 found two rules (`check.ipd-priority-required`, `check.ipd-work-kind-required`) that ARE staged toward `error` by `lkexaw` E-04's recorded obligation, which is a real pending promotion this plan deliberately does not perform. It is not an obligation this plan creates or drops: it predates this plan, belongs to `lkexaw`'s own end-state clause, and is discharged when the pending corpus no longer needs the sentinel. OQ-03 records why un-gating them HERE is nonetheless correct (`aw ipd lint`/`aw ipd begin` enforce the requirement independently, measured), and E-07 records the interaction in the code so a later reader does not mistake `warning` at this gate for a permanent exemption.
  - Carrier-Declined: The promotion obligation is NOT this plan's and is not created or dropped by it: it is `lkexaw` E-04's own recorded end-state clause, written into that executed plan before this plan existed, and this plan re-tiers nothing. Declared here only so the interaction is visible. DISCLOSED HONESTLY, because it is the one weakness of this decline: that obligation lives in an executed plan's prose and in no live backlog item or spec, so nothing will remind anyone to perform it. Raised to the maintainer in the review report rather than filed unilaterally, since creating a tracking item is a records mutation a review may not make.

## Scope check

- Over-scope: none. Only `work_cmd.py` (the predicate, its two call sites, the docstrings, and E-07's comment), one new test module, and one CHANGELOG line. RE-VERIFIED AT REVIEW: `grep -n "_validate_plan_via_engine" agent_workflows/*.py` still shows exactly the definition plus the two calls in `run_work_begin` and `run_commit`, so the caller set the plan assumed is unchanged at HEAD `de94e2dc`.
- Under-scope: if the executor finds a THIRD caller of `_validate_plan_via_engine`, update it in the same change and record which file it lived in. If that caller is outside `work_cmd.py` the edit is OUT OF SCOPE BUT NOT FORBIDDEN: make it and JUSTIFY it, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` for the added path (the earlier instruction to STOP over this is the scope-fence wording the 2026-09-01 maintainer ruling says not to use, since a fence is a declaration the runner reconciles afterwards).
- NO RULE IS RE-TIERED AND NO OTHER MODULE IS TOUCHED. `check_engine.py` stays unedited: F-3's survey found no `warning` rule that relies on blocking commits, and F-8's two staged rules keep their `warning` tier here, with their promotion to `error` left to whoever owns `lkexaw`'s end-state obligation. E-07 is a comment in a file already in scope, not a second module.

## Required tests / validation

- Targeted: `python3 -m pytest tests/test_work_gate_severity.py -o addopts="" -q`, all passing.
- Mutation check: revert only the E-02 predicate to the `== "info"` skip (locally, not committed) and show the two warning-passes cases FAIL, then restore.
- Bare suite: `python3 -m pytest`, summary line pasted.

## Spec / documentation sync

- N/A for specs: no `.spec.md` specifies the `aw commit`/`aw work begin` severity predicate (`grep -rln "aw commit\|work begin" .aw/records/specs` hits only the invariant catalog `pqsx96`, whose I-01 row is about path scoping, and `c4gd2h`, which is about runner quit), so no spec is amended.
- `CHANGELOG.md` gets one `Fixed:` bullet (E-05). The `aw commit` CLI help ("run the shared policy engine") stays accurate and is not edited.

## Open questions

### OQ-01: Should `aw commit` / `aw work begin` gate on plan findings at `error` severity only?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: YES, resolved from repository evidence. Every `warning` RuleSpec comment that speaks to commits or lifecycle gates says `warning` must not block them (`check.review-decision-unescalated`: "adds no LIFECYCLE gate (no ... begin/finalize refusal ...)"; `check.review-dangling`: "must not block a commit"; `check.graduated-to-repeated`: "visible without blocking a commit"), and none says the opposite (F-3). The predicate is fail-closed on anything not positively recognized as `warning`/`info`, so an unregistered rule (default `error`) still refuses. Warnings are printed, not dropped, so the agent still sees them.
- Carrier-Declined: Resolved here with no residual work.

### OQ-02: Should they gate on structural lint at all, given `aw ipd begin`/`finalize` own that checkpoint?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: The question is already answered by the registry for structural lint specifically: the whole-family lint umbrella `check.ipd-lint-diagnostic` is registered `info` (`k9awrq` D5 workaround, and its RuleSpec cites I-05 whose control is `aw ipd lint` itself), so it never gated and still will not. What remains in the gate is `error`-class ENGINE findings (for example `check.name-nonconformant`, which the deleted `test_work_begin_fails_closed_on_findings` pinned), which are the "validate before mutate" design of executed plan `8dto0g` E-01 and are not duplicated by `aw ipd begin`. Default: keep the gate for `error` findings. Removing it is a maintainer choice this plan does not make.
- Carrier-Declined: Resolved with a stated default; no residual work.

### OQ-03: Two of the reaching `warning` rules are STAGED toward `error`. Does making `warning` non-blocking here wrongly un-gate a requirement the repository decided to enforce?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: NO, resolved at review (`/plan-review` 2026-09-25, decision D-2) from repository evidence, not from the author's preference. `check.ipd-priority-required` and `check.ipd-work-kind-required` (F-7) are registered `warning` as a ROLLOUT STAGE whose recorded end state is `error` (`lkexaw` E-04: "nothing may leave the rule permanently at `warning`"), so the question is real. Three facts answer it. FIRST, THE REQUIREMENT IS NOT UN-GATED, it is enforced by the gate that OWNS it: measured at review, a fieldless `approved` plan yields `IPD-M110`/`IPD-M111` from `aw ipd lint` at BOTH `author` and `pre-execution`, and `aw ipd begin` refuses outright ("pre-execution gate did NOT conform (error); no receipt written"), so the plan cannot reach execution regardless of what `aw commit` does. SECOND, THE STAGING IS PRESERVED RATHER THAN DEFEATED: this plan re-tiers nothing, so the day those rules become `error` they block this gate again automatically and correctly, which is the intended end state and not a regression. THIRD, THE ALTERNATIVE IS WORSE AND SELF-CONTRADICTORY: keeping `warning` blocking to preserve these two rules' current effect would also keep every FUTURE advisory rule blocking, which is the exact trap this plan exists to close, and it would leave the gate's behavior dependent on a rollout stage rather than on a severity contract. The cost, stated because it is real: between now and that promotion, a plan missing Priority or Work-Kind can be COMMITTED (it still cannot be EXECUTED). That is the correct division of labour, since `aw commit` gates the commit and `aw ipd begin` gates execution. Reversible: yes (the predicate is one partition in one function). E-07 records the interaction in the code so the next reader is not misled.
- Carrier-Declined: Resolved at review from measured evidence (D-2); the interaction is recorded by E-07 in this plan, and the rules' promotion to `error` remains `lkexaw`'s own recorded obligation rather than a new one this plan creates.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the probe's output lines showing `check.review-decision-unescalated` (severity `warning`) produces `aw commit: refusing - 1 finding(s)` with rc 1 at the executing HEAD, the error-case line, and the `git rev-parse --short HEAD` value. ALSO paste the re-derived enriched `check_type(root, "plans")` list for the fixture plan with every `warning` rule in it named (E-01's second half), and state for each whether E-02 is the intended outcome; a `warning` rule in that list which this plan has not considered is a STOP-and-report condition, not something to absorb silently.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff --stat` limited to `agent_workflows/work_cmd.py` and the diff hunk of `_validate_plan_via_engine` showing the partition (blocking = severity not in `warning`/`info`); paste `grep -n "_validate_plan_via_engine" agent_workflows/*.py` showing only the definition and the two updated call sites.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_work_gate_severity.py -o addopts="" -q -k commit` summary showing the four commit cases passed; then paste the same command FAILING (at least the warning-commits case) with the E-02 predicate locally reverted to `if enriched.severity == "info": continue`, and the passing re-run after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_work_gate_severity.py -o addopts="" -q -k begin` summary showing the three begin cases passed; paste the warning-begin case FAILING under the same local predicate revert; confirm in the pasted test source that case (c) does not patch `check_type`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff CHANGELOG.md` showing exactly one added `- Fixed:` bullet, and the dash check as `git diff CHANGELOG.md | grep -n $'\u2014\|\u2013' || echo "no em/en dash"`, pasted showing `no em/en dash`. Do NOT use a bare `grep -c` and expect `0` with a zero exit: `grep -c` prints `0` but EXITS 1 on no match (F-9), so under `set -e` or an `&&` chain the passing case reads as a failure.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the actual final summary line of the bare `python3 -m pytest` run (e.g. `N passed, M skipped ... in Xs`), with any failure named and shown to be unrelated to this change (reproduced on the base commit) or fixed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `git diff agent_workflows/work_cmd.py` hunk containing the new comment, showing it names both `check.ipd-priority-required` and `check.ipd-work-kind-required`, the `lkexaw` end-state-is-`error` obligation, and the distinction between this lifecycle gate and the `aw check` exit code; paste `git diff --stat` showing only the three declared Scope-Paths files; and paste `python3 -c "from agent_workflows import check_engine as ce; print([ (v.severity,k) for k,v in ce.RULE_REGISTRY.items() if k in ('check.ipd-priority-required','check.ipd-work-kind-required') ])"` showing BOTH still `warning`, proving no rule was re-tiered by this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. All three open questions are `resolved` and `Blocking: no`, so the maintainer's remaining decision is approval itself.

WHAT A HUMAN IS APPROVING, stated because the diff is small and the blast radius is not. This changes what `aw commit` and `aw work begin` REFUSE, on the same commit path every agent in this repository is obliged to use. The change is one partition in `_validate_plan_via_engine` plus its two call sites, and its effect is: an `error`-class plan finding still refuses both verbs exactly as today; a `warning` finding no longer refuses and is printed instead; `info` stays silent; anything the gate cannot positively recognize as `warning`/`info` refuses (so an unregistered rule, which `enrich_drift` stamps `error` from `_DEFAULT_RULESPEC`, still fails closed). The measured practical effect at review HEAD is that a plan missing `- Priority:`/`- Work-Kind:` can be COMMITTED where today it cannot, while remaining un-EXECUTABLE because `aw ipd lint`/`aw ipd begin` refuse it independently (OQ-03, F-8). Nothing about the `aw check` exit-code contract changes: `warning` still fails CI.

SCOPE FENCE (a DECLARATION, not a stop condition): the only files expected to change are the three in `- Scope-Paths:`. `check_engine.py` is declared OUT, no rule is re-tiered, and `artifact_core.drift_exit_code` is not touched. An out-of-scope edit is not forbidden, it is ACCOUNTABLE: make it if the work requires it and then justify it, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.

TEST HONESTY (hard MUST): every test claim pastes the ACTUAL runner output, including each mutation run. Run the suite BARE as `python3 -m pytest`; do not add `-n0` (disables xdist and multiplies runtime here), a second `-q` (compounds into `-qq` and suppresses the `N passed` summary this contract requires), or `-p no:randomly`. When a narrowed run needs per-test counts, clear the configured defaults with `-o addopts=""` rather than fighting them flag by flag.

The executor commits only the paths in `- Scope-Paths:` via `aw commit <plan> -- agent_workflows/work_cmd.py tests/test_work_gate_severity.py CHANGELOG.md`, never `git add -A`, and never pushes.

STOP AND REPORT on either of two genuinely unsafe conditions: E-01 shows the `warning` case ALREADY commits (the defect is fixed, so this plan should be RETIRED to `superseded/` with the reason, not executed); or E-01's re-derived reachable set contains a `warning` rule this plan has not considered (a rule whose un-gating may be a maintainer decision rather than this plan's). A scope question is NOT such a condition.

On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which is owned by the RUNNER when a runner executes this plan in a managed lane and otherwise performed by the executor with `aw ipd finalize`.
