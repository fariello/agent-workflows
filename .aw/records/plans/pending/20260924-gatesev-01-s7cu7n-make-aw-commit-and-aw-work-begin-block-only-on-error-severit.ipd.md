# IPD: Make aw commit and aw work begin block only on error-severity plan findings, so a warning rule cannot silently acquire commit-blocking authority

- Date: 2026-09-24
- Kind: child
- Concern: `work_cmd._validate_plan_via_engine`, which backs BOTH `aw work begin` and `aw commit`, keeps every plan finding whose severity is not exactly `info`, so any rule registered `warning` silently acquires commit-blocking and begin-blocking authority the moment it fires on a plan, contradicting every `warning` RuleSpec comment in `check_engine` that says the tier adds no lifecycle gate and must not block a commit.
- Scope: IN: change the gate predicate in `work_cmd` so only `error`-class findings (including the conservative `_DEFAULT_RULESPEC` `error` for an unregistered rule, and any unrecognized severity string, which fails closed) refuse; print `warning` findings as a named, non-blocking advisory on both verbs instead of dropping them; keep `info` silent as today; add a new test module covering warning-commits-with-advisory and error-still-refuses for both verbs; one CHANGELOG line. OUT: `artifact_core.drift_exit_code` and the `aw check` exit-code contract (a different contract where `warning` deliberately fails CI); re-tiering any rule's severity; removing the plan-findings gate altogether (OQ-02); rewording `check_engine` comments that describe the exit-code contract.
- Scope-Paths: agent_workflows/work_cmd.py, tests/test_work_gate_severity.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Set: gatesev
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: s7cu7n
- From-Backlog: 7a53rm
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 7a53rm; re-measured at HEAD 877545fc that a registered `warning` finding located at the plan makes `aw commit` exit 1 with "refusing", and that of the nine `warning` rules only `check.review-decision-unescalated` is actually reachable from the gate's `check_type(repo_root, "plans")` call today (the other eight run only in the `check_types` full sweep).

## Goal

Make the plan-findings gate in `aw commit` and `aw work begin` honor the three-tier severity model the rest of the engine documents: `error` refuses, `warning` is printed as a visible advisory that does not refuse, `info` stays silent. This removes the trap where registering a deliberately advisory `warning` rule silently changes what `aw commit` refuses (measured by `k9awrq` when `check.ipd-lint` at `warning` broke four commit/begin tests).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the defect before changing it

- [ ] E-01 RE-MEASURE the defect at the executing HEAD before editing. Run a throwaway probe (under `/tmp`, not committed) that builds a tmp git repo with one conformant pending plan (`- Scope-Paths: src/`), patches `agent_workflows.check_engine.check_type` to return one `artifact_core.Drift(str(plan), "check.review-decision-unescalated", "probe")`, and drives `cli.main(["commit", "<id6>", "--dir", <root>, "-m", "m", "--", "src/f.py"])`. At authoring this printed `aw commit: refusing - 1 finding(s) on ...: check.review-decision-unescalated: probe` with rc 1. Repeat with `check.name-nonconformant` (error) to show the same refusal. Also confirm `check_engine.rule_spec("check.review-decision-unescalated").severity == "warning"`. If the warning case already commits, STOP: the defect is fixed and this plan should be retired, not executed.
  - Depends on: none
  - Expected outcome: pasted probe output showing a `warning` finding refuses `aw commit` (rc 1) at the executing HEAD, and the error case also refuses.
  - Execution state: pending

### Task group 2: fix the predicate

- [ ] E-02 In `agent_workflows/work_cmd.py`, change `_validate_plan_via_engine` to PARTITION the plan's enriched findings instead of filtering only `info`: return `(blocking, advisory)` where `advisory` holds findings whose severity is exactly `warning`, `info` findings are dropped as today, and `blocking` holds EVERYTHING ELSE (so `error`, an unregistered rule that `check_engine.enrich_drift` stamps with `_DEFAULT_RULESPEC`'s `error`, an empty severity, and any unrecognized severity string all refuse: the gate fails closed on anything it does not positively recognize as advisory). Update both call sites, `run_work_begin` and `run_commit`: refuse (rc 1, unchanged "refusing" message and per-finding lines) only on a non-empty `blocking`; when `advisory` is non-empty, print one header line naming the count, the plan, and that it is not blocking (e.g. `aw commit: note - 1 advisory (warning) finding(s) on <plan> (not blocking):`, and the `aw work begin:` equivalent), followed by `  <rule>: <detail>` per finding, BEFORE proceeding. Print advisories even when also refusing, so the operator sees the full set. Update the function docstring, the `# Validate BEFORE mutating` comment in `run_work_begin`, and the module docstring bullet `(fail closed on findings)` to say "fail closed on error-severity findings; warnings are printed as advisories". Do NOT touch `artifact_core.drift_exit_code`.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/work_cmd.py` shows the partition, both call sites updated, docstrings aligned; no other module changed.
  - Execution state: pending

### Task group 3: tests

- [ ] E-03 CREATE `tests/test_work_gate_severity.py` (the former `tests/test_work_primitives.py`, which encoded the begin/commit behavior, was deleted by commit `19313eed` "test: trim test suite", so there is no existing test to edit). Build a tmp git repo fixture modelled on the deleted module's `WorkPrimitivesTest.setUp` (retrievable with `git show 19313eed^:tests/test_work_primitives.py`): a conformant approved plan `20260828-wk-01-wk0001-demo.ipd.md` with `- Scope-Paths: src/, tests/`, `.gitignore` for `.aw/worktrees/` and `.aw/state/`, an initial commit. If the tests exercise `aw work begin`, declare the execution role via `tests.support.declare_execution_role` or `coordinator_role` as the other lifecycle tests do, so an ambient worker marking cannot change the outcome. `aw commit` cases: (a) a patched `check_engine.check_type` returning one `check.review-decision-unescalated` Drift at the plan path: rc 0, output contains `advisory` and the rule id, and `git show --stat HEAD` contains the committed path; (b) the same with `check.name-nonconformant`: rc 1, output contains `refusing` and the rule id, HEAD unchanged; (c) an UNREGISTERED rule id (e.g. `check.gatesev-probe-unregistered`): rc 1, proving fail-closed on the default `error`; (d) one warning plus one error: rc 1, and the output names BOTH rules.
  - Depends on: E-02
  - Expected outcome: the new module's `aw commit` cases pass against the fix, and cases (a) FAILS when the E-02 predicate is reverted to the `== "info"` skip.
  - Execution state: pending

- [ ] E-04 In the same module, add `aw work begin` cases: (a) the `warning` Drift: rc 0, output contains `allocated worktree` and `advisory`, and `.aw/state/work/wk0001/work-lease.json` exists; (b) the `error` Drift: rc 1, output contains `refusing to start`, and NO lease file exists; (c) one UNPATCHED end-to-end error case mirroring the deleted `test_work_begin_fails_closed_on_findings`: a second plan named `badname.ipd.md` with `- Id: bad001` genuinely trips `check.name-nonconformant`, and `aw work begin bad001` refuses with rc 1 and no lease. Case (c) guards against the patching seam diverging from the real engine.
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
- COMMITS go through `aw commit <plan> -- <paths>`; tests run bare as `python3 -m pytest`; when a narrowed run needs per-test counts use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All re-measured at HEAD `877545fc` (`git rev-parse --short HEAD`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `work_cmd._validate_plan_via_engine` | CONFIRMED. The gate drops only `info`; a `warning` finding at the plan path refuses `aw commit` exactly like an `error`. | Code: `if enriched.severity == "info": continue  # advisory nudge, not a blocking finding`. Probe (patched `check_type`, real `cli.main(["commit", ...])`): `check.review-decision-unescalated warning rc= 1 \| ['aw commit: refusing - 1 finding(s) on 20260828-wk-01-wk0001-demo.ipd.md:', '  check.review-decision-unescalated: probe']`; `check.name-nonconformant error rc= 1` identical shape. Direct: `check.setid-length-warn warning blocks= True`, `check.ipd-draft-ready-to-review info blocks= False`. |
| F-2 | MED (narrows the claim) | `check_engine.check_type` vs `check_engine.check_types` | THE "NINE WARNING RULES BLOCK COMMITS TODAY" FRAMING IS OVERSTATED. `python3 -c "... [v.severity, k] for RULE_REGISTRY if severity != 'error'"` lists nine `warning` rules (graduated-to-repeated, identity-absent-from-name, orphaned-live-blocker, review-dangling, review-decision-unescalated, setid-length-warn, stale-index-stale, system-layout-drift, system-layout-missing). But the gate calls `check_type(repo_root, "plans")`, and a spy over every `check_*` callable showed only `check_review_decision_unescalated` is reached; `check_setid_length`, `check_review_dangling`, `check_release_gates`, `release_gate_warnings`, `check_system_layout`, `check_name_identity` are `NOT reached` (they run in `check_types`' full-sweep seam). `check.stale-index-stale` is emitted by `plans_index.check_drift`, which `check_content` calls only when `include_retired` is true, and the gate does not pass it. So today exactly ONE warning rule can block, and only when its finding is located at the plan (the irreversible-unescalated branch; the malformed-review and missing-`Reversible` branches locate at the review path and are filtered out). The DEFECT is still real because it is a latent trap for any future plan-scoped `warning` rule, which is precisely what `k9awrq` hit. | spy probe output quoted; `check_engine.check_types` comments "rides this once-per-full-sweep seam"; `check_review_decision_unescalated` emits `_core.Drift(str(plan_path), _REVIEW_DECISION_RULE, ...)` only for the unescalated-irreversible branch |
| F-3 | INFO | `check_engine.RULE_REGISTRY` | NO `warning` rule was registered in order to block commits. Every `warning` RuleSpec comment that addresses commits says the opposite (see Step 0). The one rule deliberately chosen to be non-`info` for a real obligation (`check.review-decision-unescalated`) justifies that choice by EXIT CODE, not by a commit gate. So no rule needs to be raised to `error` as part of this fix. | quotes in Step 0; `grep -n "block.\{0,20\}commit" agent_workflows/check_engine.py` hits: "it must not block a commit or set an exit code", "should be visible without blocking a commit" |
| F-4 | INFO | `tests/test_work_primitives.py` | THE TEST FILE THE BACKLOG ITEM NAMES NO LONGER EXISTS. It was deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 896 lines removed). No remaining test drives `run_commit`'s or `run_work_begin`'s findings gate (`grep -rn "run_work_begin\|_validate_plan_via_engine" tests/` is empty). So nothing encodes the old behavior and nothing currently guards the new one; E-03/E-04 create the coverage. | `git show 19313eed --stat \| grep work_prim` -> `tests/test_work_primitives.py \| 896 -----` |
| F-5 | INFO | `check_engine.check_content` comment | A comment beside `check_review_decision_unescalated` says "Advisory (`warning`), so it never sets an exit code", which is false for the exit code (`drift_exit_code` exempts only `info`) and was the other source of confusion. Not this plan's contract; recorded in Deferred. | quoted comment text in `check_content`'s plans branch |
| F-6 | INFO | `8dto0g` (executed) | The original design intent is "fail closed on any blocking finding" with "advisory info-severity nudges excluded"; it never defined `warning` as blocking, it just predates the third tier being used for plan-scoped rules. Fail-closed is preserved by making the blocking set "everything not positively advisory". | `8dto0g` E-01 execution note: "filtered to the plan (advisory info-severity nudges excluded) and fails closed on any blocking finding" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures that a `warning` finding refuses `aw commit` at the executing HEAD (STOP if already fixed).
2. E-02 partitions findings in `work_cmd._validate_plan_via_engine` into blocking (everything not `warning`/`info`) and advisory (`warning`), and makes both verbs refuse only on blocking while printing advisories.
3. E-03 adds `aw commit` tests: warning commits and prints the advisory; error, unregistered rule, and mixed warning+error refuse.
4. E-04 adds `aw work begin` tests: warning allocates and prints the advisory; patched error and a real misnamed plan refuse with no lease.
5. E-05 records the behavior change in `CHANGELOG.md`.
6. E-06 runs the bare suite.

## Deferred / out of scope (with reason)

- CHANGING `artifact_core.drift_exit_code` OR THE `aw check` EXIT CONTRACT. `warning` failing a CI exit is deliberate and documented (`check.system-layout-*` RuleSpec comment); only the lifecycle action gate is wrong.
  - Carrier-Declined: Intended behavior of a different contract, not an outstanding obligation.
- REMOVING THE PLAN-FINDINGS GATE FROM `aw commit`/`aw work begin` ENTIRELY (the backlog's question 2). Resolved as OQ-02 default: keep it for `error` findings.
  - Carrier-Declined: Resolved in OQ-02 on repository evidence; revisiting is a maintainer choice with no open obligation.
- CORRECTING THE FALSE "so it never sets an exit code" COMMENT in `check_engine.check_content` (F-5). It is a comment about the exit-code contract in a file outside this plan's scope; a one-line comment fix is cheap but widening scope into `check_engine.py` for it invites contention with the many plans that touch that file.
  - Carrier-Declined: Cosmetic comment inaccuracy about a different contract; the RuleSpec comments beside it already state the correct behavior ("DO NOT READ `warning` AS 'cannot fail anything'"), so no reader is misled without also seeing the correction.
- RE-TIERING ANY RULE. F-3 found no `warning` rule that relies on blocking commits, so none is raised to `error`.
  - Carrier-Declined: No rule depends on the old behavior (F-3); nothing to carry.

## Scope check

- Over-scope: none. Only `work_cmd.py`, one new test module, and one CHANGELOG line.
- Under-scope: if E-01 finds another caller of `_validate_plan_via_engine` beyond `run_work_begin` and `run_commit` (none at authoring: `grep -n "_validate_plan_via_engine" agent_workflows/*.py` shows the definition and those two calls), update it in the same change and record it; if that caller lives outside `work_cmd.py`, STOP and declare the path first.

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the probe's output lines showing `check.review-decision-unescalated` (severity `warning`) produces `aw commit: refusing - 1 finding(s)` with rc 1 at the executing HEAD, the error-case line, and the `git rev-parse --short HEAD` value.
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
  - Required evidence: paste `git diff CHANGELOG.md` showing exactly one added `- Fixed:` bullet, and `git diff CHANGELOG.md | grep -c $'\u2014\|\u2013'` printing `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the actual final summary line of the bare `python3 -m pytest` run (e.g. `N passed, M skipped ... in Xs`), with any failure named and shown to be unrelated to this change (reproduced on the base commit) or fixed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. Both open questions are resolved from repository evidence and `Blocking: no`. The executor commits only the paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>` (never `git add -A`, never push) and pastes actual runner output for every test claim. STOP if E-01 shows the warning case already commits. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which is owned by the runner when a runner executes this plan in a managed lane and otherwise performed with `aw ipd finalize`.
