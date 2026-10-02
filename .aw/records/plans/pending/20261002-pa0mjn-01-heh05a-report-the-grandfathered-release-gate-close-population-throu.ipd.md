# IPD: Report the grandfathered release-gate close population through an opt-in advisory surface

- Date: 2026-10-02
- Kind: child
- Concern: The release-gate close backstop now HAS a whole-tree arm, but it grandfathers per item against a cutover date, and on this tree the cutover (`2026-10-01`) is LATER than the newest illegitimate close (`2026-09-26`), so the arm skips the ENTIRE 53-item historical population and no shipped surface reports it. The backlog item's own diagnosis ("staged-scoped in every caller") is therefore STALE: `check.blocking-item-closed-without-gate` is no longer staged-only, yet its finding population on this tree is still exactly zero while 53 items on disk receive an `error` verdict from the shipped predicate. The question the item asks is still live and the answer it proposes is still the right shape; only the mechanism has moved.
- Scope: Decide and implement the reporting surface for the GRANDFATHERED residue: items the at-rest arm deliberately skips because they closed before the cutover, but which the close predicate judges illegitimate. Ship (a) a new `info`-severity advisory rule reporting that population whole-tree, registered in `RULE_REGISTRY` so its severity is contractual rather than defaulted; (b) an opt-in plumbing path so the population is reportable on demand without changing any default exit code; and (c) behavioral tests over synthetic fixtures pinning both the advisory's findings and the unchanged default. EXCLUDES mutating ANY closed backlog record (no gate written onto, cleared from, or re-asserted on a `done` item), because `AGENTS.md` states the gate rule governs LIVE items only and that gating an already-done item "would assert a history that did not happen". EXCLUDES changing `evaluate_blocking_close`, its three legitimacy paths, `_carrier_is_executed`, or the severity of the existing `check.blocking-item-closed-without-gate`. EXCLUDES moving the repository's `release_gate_at_rest` cutover date, which would retroactively convert all 53 into exit-blocking errors and is the exact blast radius this plan exists to avoid. EXCLUDES the per-item adjudication of WHICH of the 53 are genuine drops, which is plan `1hrlp3`'s deliverable.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/cli.py, tests/test_check_engine_release_gate.py, AGENTS.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: pa0mjn
- Set: pa0mjn
- Order: 1
- Highest E allocated: 06
- Author: aw oc run model=opencode
- Id: heh05a

## Workflow history

- 2026-10-02 to-review (aw oc run model=opencode): authored from backlog `pa0mjn`. CORRECTS the item's central mechanical claim: an at-rest whole-tree arm shipped in `gateatrest` Order 02 (`b24o3q`, executed) after the item was filed, so the rule is NOT staged-scoped any more; the population is invisible for a DIFFERENT reason (cutover-based per-item grandfathering). Population re-measured on this tree. See `## Findings`.

## Goal

Make the grandfathered illegitimate-close population VISIBLE on demand, without turning `aw check` or CI red on 53 historical items and without mutating a single closed record. The deliverable is a reporting surface plus the decision the backlog item asks for, recorded with its evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish the baseline the design rests on

- [ ] E-01 RE-MEASURE THE POPULATION AND THE GRANDFATHERING BOUNDARY BEFORE WRITING ANY RULE, and record both in `## Findings` as an executor-dated row rather than trusting this plan's authoring-time numbers. This is the first item for a specific reason: the backlog item's premise was ALREADY INVALIDATED ONCE between filing and authoring (by `b24o3q` shipping the at-rest arm), so a third change landing before execution is a live possibility, and every design choice below is conditional on the boundary still skipping the whole population. Measure, with the shipped code and not a reimplementation: the count of `done` backlog items whose `- Status:` metadata reads `done` and which carry `- Blocks-Release:`; among those, the count receiving `legitimate=False` with `severity == "error"` from `check_engine.evaluate_blocking_close`; the value `config.resolve_cutover_date(repo, "release_gate_at_rest", compact=True)` returns; and the MAXIMUM close date among the illegitimate set via `check_engine._item_close_date`. Use `check_engine._from_backlog_carrier_index` for the carrier question and pass it as `carrier_index=`, because `find_from_backlog_artifacts` re-walks the plans and specs trees on EVERY call and that helper's own docstring records a 54x measurement for exactly this mistake. THE DECISION BRANCH THIS CREATES, stated now so the executor does not have to invent one: if the measured maximum close date is still EARLIER than the cutover, proceed with E-02 onward as written; if a cutover change or a new illegitimate close has made some of the population already reportable as `error`, STOP, record the new measurement, and raise it as a blocking question rather than shipping an advisory whose population is now partly exit-blocking (a finding reported at two severities through two rules is a defect, not a feature).
  - Depends on: none
  - Expected outcome: a dated measurement row in `## Findings` carrying the five numbers and an explicit statement of which branch of the decision applies, with the shipped-symbol invocation that produced them.
  - Execution state: pending

### Task group 2: the advisory rule

- [ ] E-02 REGISTER A NEW `info`-SEVERITY RULE `check.blocking-close-grandfathered` IN `check_engine.RULE_REGISTRY`, with `ASSURANCE_REPOSITORY`, `DET_DETERMINISTIC`, and invariant `I-07`, and with a block comment stating WHY the severity differs from its `error`-severity sibling. `info` IS LOAD-BEARING AND `warning` WOULD NOT WORK: `artifact_core.drift_exit_code` returns 1 for ANY finding whose severity is not `info` ("an `info`-severity finding is ADVISORY ... and does NOT fail the gate; only error/warning-class findings drive the nonzero exit"), so registering this at `warning` would turn `aw check` and CI red on the whole historical population, which is the precise outcome the backlog item identifies as wrong. NOTE THE ITEM'S OWN SUGGESTION IS MECHANICALLY WRONG HERE AND MUST NOT BE FOLLOWED LITERALLY: it proposes following `check.orphaned-live-blocker`, which is registered `warning`, and that rule avoids the exit code NOT by its severity but by being returned from the separate `release_gate_warnings` function that the exit-blocking sweep never calls (its docstring: findings that "NEVER set an exit code (returned separately from the exit-blocking `check_release_gate_consistency`)"). Both routes exist; this plan takes the `info` route, and E-03 states why the `release_gate_warnings` route was rejected. Registration is NOT bookkeeping: an unregistered rule id falls back to `_DEFAULT_RULESPEC` at `error` severity with an empty invariant, so omitting the entry would silently make this advisory exit-blocking, which is the same defect in a different place. Follow the in-file precedent of `check.collisions-not-checked`, whose comment records the same reasoning for choosing `info` over a flag or an error.
  - Depends on: E-01
  - Expected outcome: `check_engine.RULE_REGISTRY["check.blocking-close-grandfathered"]` exists at `info` severity with invariant `I-07`, and `artifact_core.drift_exit_code` returns 0 for a drift list containing only that rule.
  - Execution state: pending

- [ ] E-03 IMPLEMENT THE RULE AS A THIRD ARM OF `check_engine.check_release_gate_consistency`, gated behind a NEW keyword-only parameter (`grandfathered: bool = False`), reusing the at-rest arm's candidate walk rather than adding a second one. The arm is the at-rest arm's COMPLEMENT and must be implemented as such: the at-rest arm keeps candidates where `cdate is not None and cdate >= cutover`, so this arm takes exactly those it drops, namely a `done`+gated item whose close date is EARLIER than the cutover, plus (stated explicitly because it is a real third case) one whose close date is UNDATABLE, which `_item_close_date` returns `None` for. Deduplicate against `seen_blocking_locations` exactly as the at-rest arm does against the staged arm, so an item can never be reported by two rules in one run. Emit one `_core.Drift` per finding with the rule id from E-02 and a detail that states the item is GRANDFATHERED and names the boundary it predates, so a reader is not told to "fix" something policy deliberately exempts; the detail must not recommend `aw backlog set done`, because for an already-closed item that remedy is the mutation `AGENTS.md` forbids. WHY A PARAMETER ON THE EXISTING FUNCTION RATHER THAN A NEW `release_gate_warnings`-STYLE FUNCTION: the candidate walk, the `_status_meta`/`_META_BLOCKS_RELEASE_RE` filters, the shared carrier index and the dedup set already exist in this one function, and a second function would have to duplicate all four or re-walk the corpus, which is the measured defect E-01 cites. The default `False` is what preserves every current caller's behavior: `check_commit_invariants` and the opt-in hook call this function positionally with no keyword, so they are unchanged by construction.
  - Depends on: E-02
  - Expected outcome: `check_release_gate_consistency(repo, grandfathered=True)` returns one `check.blocking-close-grandfathered` drift per pre-cutover illegitimate close, the same call with the default returns none of them, and no item appears under both rules in a single call.
  - Execution state: pending

- [ ] E-04 PLUMB AN OPT-IN CLI PATH so the population is reachable from a command, following the established flag precedent rather than inventing a surface. Add a `--grandfathered` flag to `aw check` (dest `grandfathered`, `action="store_true"`), modelled on the adjacent `--strict-setid-length` flag, whose comment states the same shape of contract: "Without either, grandfathering is per artifact against `cutovers.setid_length`". Thread it to `check_engine.check_release_gates`, which is the function the `release-gates` target calls and which already passes `at_rest=True`, and from there into the E-03 parameter. DO NOT REUSE THE EXISTING `--all` FLAG, even though it is superficially close ("Include retired, archived, and terminal artifacts") and is already read into `include_retired`: it is consumed by `check_types`/`_iter_type_files` to widen which FILES are enumerated, and overloading it to also switch on a distinct rule family would make one flag mean two unrelated things and would change the finding set of every `aw check --all` invocation in the repository, including CI's. A separate flag changes nothing for anyone who does not pass it. Because the rule is `info`, a run that DOES pass the flag and finds the whole population still exits 0, so the flag is safe to add to a CI step for visibility without making CI fail; state that property in the help text rather than leaving a reader to derive it.
  - Depends on: E-03
  - Expected outcome: `aw check release-gates --grandfathered` reports the population as `info` findings and exits 0; `aw check release-gates` with no flag reports zero findings and exits 0, byte-identically to today.
  - Execution state: pending

### Task group 3: pin the behavior and correct the record

- [ ] E-05 EXTEND `tests/test_check_engine_release_gate.py` WITH BEHAVIORAL CASES over synthetic temp repos, reusing the `_create_minimal_repo` fixture builder the file already uses for the at-rest arm's five cases (`test_rule_blocking_item_closed_at_rest_committed_unstaged` and its siblings each stamp `{"cutovers": {"release_gate_at_rest": "2026-10-01"}}` into `.aw/config/project.json`, which is exactly the knob these cases need to move). Cover, at minimum, one case per discriminating behavior: a pre-cutover illegitimate close reported under `check.blocking-close-grandfathered` when `grandfathered=True`; the SAME fixture reporting NOTHING under the default, which is the regression guard that keeps this plan from changing any existing exit code; a post-cutover illegitimate close still reported under `check.blocking-item-closed-without-gate` and NOT under the new rule, proving the two arms partition rather than overlap; an item with no datable close record landing in the new rule; an ungated `done` item reported by neither; and a pre-cutover item with an EXECUTED same-gate carrier reported by neither, since the predicate finds that close legitimate and an advisory that flags legitimate history would train people to ignore it. ASSERT THE EXIT-CODE PROPERTY DIRECTLY, not by proxy: call `artifact_core.drift_exit_code` on the returned drift list and assert 0, because that is the single claim the whole design rests on and a severity string assertion would not catch a future registry regression. Every assertion is an OUTCOME assertion on returned drift lists, rule ids, and exit codes. Do NOT read `check_engine.py` with `inspect`, `ast`, regex or substring search, do NOT assert caller counts or symbol censuses, and do NOT pin a docstring or comment banner (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16). THE SYNTHETIC-FIXTURE CHOICE IS DELIBERATE: an assertion on this repository's live count of 53 would be a pin against a moving corpus that any unrelated lane could break, so the live number belongs in `## Findings` and in E-06's prose, never in an assertion.
  - Depends on: E-04
  - Expected outcome: new cases in the existing test file pass, each discriminating one branch, including an explicit `drift_exit_code == 0` assertion and a default-call case proving the unflagged finding set is unchanged.
  - Execution state: pending

- [ ] E-06 CORRECT THE `AGENTS.md` SENTENCE THAT NOW UNDER-STATES THE RULE'S REACH, and record the DECISION the backlog item asks for in the same place the surrounding policy already lives. The sentence to amend reads "The check rule examines every `done` backlog item on disk, grandfathered per item against the repository's stamped cutover date" (`AGENTS.md`, `## Release gates (Blocks-Release)` section). It is ACCURATE and this plan does not contradict it; what it omits is that the grandfathered residue is now REPORTABLE on demand, and that omission is why a reader concludes the population is unreachable. Add the opt-in surface and state the honest limit: the advisory is `info`, so it never sets an exit code, and it reports a population policy deliberately exempts rather than a set of defects to fix. CRITICAL PLACEMENT CONSTRAINT: verify and paste line numbers proving the target paragraph sits BELOW the `<!-- /aw:block -->` marker, because everything above it is installed from `agent_workflows/engine.py` and must not be hand-edited; the `## Release gates` section was repo-local editable text when `b24o3q` E-07 edited this same paragraph, but re-confirm rather than inheriting that, since line numbers move. CHECK FOR A CO-EDIT COLLISION BEFORE WRITING: this paragraph is contended (`b24o3q`, `2o5wka` and `47ttnv` have each edited it), so read it at execution time and edit only the clause this plan owns, reverting nothing. Do NOT restate the policy in `.aw/records/backlog/README.md`, which points at `AGENTS.md` by design.
  - Depends on: E-05
  - Expected outcome: the `AGENTS.md` release-gates paragraph names the opt-in advisory surface and its `info`/no-exit-code limit, with pasted line numbers proving the edit is below `<!-- /aw:block -->` and that no neighbouring sentence was reverted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- SEVERITY IS A REGISTRY CONTRACT, NOT A LOCAL CHOICE. `check_engine.RULE_REGISTRY` maps each rule id to a `RuleSpec` carrying severity, assurance class, determinism and invariant; an unregistered id falls back to `_DEFAULT_RULESPEC` at `error` with an empty invariant. Several in-file comments record that omitting an entry silently drops the invariant trace, so E-02 registers rather than relying on a default.
- `info` IS THE ONLY NON-EXIT-CODING SEVERITY. `artifact_core.drift_exit_code` returns 1 for any finding whose severity is not `info`; `warning` fails a gate exactly as `error` does. An in-file comment on `check.live-bug-ungated` makes the same point from the other direction, rejecting `warning` because it "would fail an exit code anyway".
- THERE ARE TWO DISTINCT WAYS A RELEASE-GATE FINDING AVOIDS THE EXIT CODE, and they must not be confused. `check.orphaned-live-blocker` is `warning` but is returned from `release_gate_warnings`, a function the exit-blocking sweep never calls. `check.collisions-not-checked` is `info` and is returned from the sweep itself. This plan takes the second route (E-02/E-03); the backlog item's suggestion to copy the first is addressed in E-02.
- THE AT-REST ARM ALREADY EXISTS AND IS CUTOVER-GATED. `check_release_gate_consistency` takes `at_rest: bool = False`; the arm resolves `release_gate_at_rest` via `config.resolve_cutover_date` and `continue`s on any candidate whose `_item_close_date` is `None` or earlier than the cutover. `check_release_gates` is the single caller passing `at_rest=True`.
- A PER-INVOCATION FLAG THAT DISABLES GRANDFATHERING IS AN ESTABLISHED SHAPE. `aw check --strict-setid-length` is exactly that for `check_setid_length`, with a repository-policy counterpart (`setids.strict`). E-04 follows its plumbing rather than inventing a surface.
- ONE SHARED CARRIER WALK, NEVER PER ITEM. `check_engine._from_backlog_carrier_index` is the single owner of "which artifacts carry a handoff for this item" and its docstring records a 54x measurement against the per-item `find_from_backlog_artifacts` form, a defect this repository has already fixed twice.
- CLOSED RECORDS ARE NOT MUTATED. `AGENTS.md` states the gate rule governs LIVE items only and that gating an already-done bug "would assert a history that did not happen"; `check_live_bug_gate`'s docstring states the same ("`done` is NEVER flagged").

## Findings

MEASURED ON THIS TREE at HEAD `5a45260b2`, driving the shipped predicate and the shipped cutover resolver over the real corpus. E-01 re-derives every number below before any code is written, because the premise this plan corrects was itself invalidated between the item being filed and this plan being authored.

| Measurement | Value |
|---|---|
| backlog items with `- Status: done` | 580 |
| of those, carrying `- Blocks-Release:` | 302 |
| of those, verdict `legitimate=False` + `severity=error` | **53** |
| reason class: no same-gate carrier at all | 46 |
| reason class: same-gate carrier(s) present, not all executed | 7 |
| `Work-Kind: bug` among the 53 | 47 (plus 3 `feature`, 2 `followup`, 1 `chore`) |
| close-date range of the 53 | `20260821` -> `20260926` |
| of the 53, undatable close record | 0 |
| resolved `release_gate_at_rest` cutover on this tree | `20261001` |
| of the 53, dated on/after the cutover (so reportable today) | **0** |
| `aw check release-gates` on a clean tree | **CONFORMS, 504 checked, 0 errors / 0 warnings / 0 info** |

- F-01 THE ITEM'S MECHANICAL DIAGNOSIS IS STALE AND MUST NOT BE CARRIED FORWARD. The item says the rule "iterates `_staged_backlog_done_items` ... so the rule is STAGED-SCOPED in every caller (the commit-invariants aggregator, the `aw check` sweep, and the opt-in pre-commit hook alike)". That was true when filed and is now FALSE for one caller: `check_release_gate_consistency` grew an `at_rest` arm (`gateatrest` Order 02, `b24o3q`, now in `.aw/records/plans/executed/` at `- Status: executed`) that walks every committed item via `backlog._iter_items`, and `check_release_gates` passes `at_rest=True`. The staged arm remains staged-scoped, and `check_commit_invariants` and the opt-in hook both still call the function with no keyword, so for THEM the item's description still holds.
- F-02 THE POPULATION IS NONETHELESS STILL INVISIBLE, FOR A DIFFERENT AND NARROWER REASON. The at-rest arm grandfathers PER ITEM against the stamped cutover, skipping any candidate whose close date is `None` or `< cutover`. Measured: the cutover resolves to `20261001` while the newest illegitimate close is `20260926`, so the arm skips all 53. This is why `aw check release-gates` reports `CONFORMS ... 0 errors 0 warnings 0 info` on a clean tree while the predicate returns 53 error verdicts over the same corpus. The item's CONCLUSION (no shipped surface reports the historical population) is therefore correct and remains the thing worth fixing; only its stated cause has moved.
- F-03 THE ITEM'S PROPOSED PRECEDENT IS THE RIGHT INSTINCT BUT THE WRONG MECHANISM. It says to add "a SEPARATE ADVISORY rule that never sets the exit code, as `check.orphaned-live-blocker` already does". That rule is registered at `warning`, and `artifact_core.drift_exit_code` fails on `warning` exactly as on `error`; what spares it is that it is returned from `release_gate_warnings`, which the exit-blocking sweep never calls. Copying the SEVERITY without the PLUMBING would produce precisely the CI-red outcome the item warns against. This plan uses `info`, following `check.collisions-not-checked`, whose own comment records choosing `info` over a flag or an error for a structurally identical "state the limit" problem.
- F-04 MOVING THE CUTOVER IS THE OBVIOUS ALTERNATIVE AND IS THE WRONG ONE. A one-line edit to `release_gate_at_rest` in `.aw/config/project.json` would make all 53 reportable immediately. It would also make them `error`-severity findings inside the exit-blocking sweep, turning `aw check` and CI red on 53 historical items at once, and `AGENTS.md` forbids the mutation that would clear most of them. The cutover's own registration comment in `config.py` states the value is "the FEATURE INTRODUCTION date, not the enforcement boundary", so it is not a severity dial and should not be used as one. Excluded in `- Scope:` for this reason.
- F-05 THE TWO ERROR BRANCHES HAVE DIFFERENT MEANINGS AND THE SMALLER ONE IS THE LEAST LIKELY TO BE A GENUINE DROP. 46 of the 53 reach the fail-closed branch (no same-gate carrier at all); the other 7 reach the distinct carrier-present-but-not-all-executed branch, which `evaluate_blocking_close` reports because its `HANDOFF` arm requires `all(...)` carriers executed (tightened by `anycarrier` `2o5wka`). An item with eight executed carriers and one superseded sibling therefore reads as an error even though the work demonstrably shipped. The two classes are distinguishable WITHOUT prose matching, by asking the carrier index directly, which is what E-03's detail text and E-05's partition cases rely on.
- F-06 THE 53 IS AN UPPER BOUND, NOT A COUNT OF PROVEN DROPS, AND THE ADVISORY'S WORDING MUST SAY SO. A `SATISFIED` close is only distinguishable on disk if the citation was PERSISTED, and persistence shipped in `gateatrest` Order 01 (`f7igdu`, executed), which added the `- Close-Evidence:` line written when `verdict.path == "SATISFIED"`. Measured: ZERO items under `.aw/records/backlog/done/` carry that line, which is expected because every one of the 53 closed before it shipped. So for this whole historical population a legitimate evidence-based close is byte-indistinguishable from a dropped gate. This is the central reason the rule must be advisory rather than an error, and the reason E-03's detail must not imply a defect.
- F-07 THE PER-ITEM ADJUDICATION IS ANOTHER PLAN'S DELIVERABLE AND IS NOT DUPLICATED HERE. Pending plan `1hrlp3` (backlog `mbjuv5`) audits this same population and reports that 48 of 53 close messages assert shipped work while only 3 carry a bare default message. That plan ships a `tools/gate_drop_audit.py` auditor and a `.findings.md` report; neither exists on this tree yet. This plan ships a CHECK SURFACE and deliberately does not re-derive the adjudication, which is why its `- Scope-Paths:` names neither path and why it declares no dependency on that plan: the advisory is correct and useful whether or not the audit lands, and the audit's conclusions would change this plan's prose but not its code.
- F-08 THE DEFAULT PATH MUST BE PROVABLY UNCHANGED, WHICH IS WHY E-05 ASSERTS IT RATHER THAN ASSUMING IT. `check_commit_invariants` calls `check_release_gate_consistency(repo_root)` positionally through a function-pointer loop, and `hooks/backlog_blocking_close_gate` filters `check_release_gate_consistency(root)` to the single `check.blocking-item-closed-without-gate` rule. Both are therefore unchanged by a keyword-only parameter defaulting to `False`, but "unchanged by construction" is an argument and not evidence, so a default-call regression case is required.

## Proposed changes (ordered, validatable)

1. `## Findings`: an executor-dated re-measurement of the population, the cutover, and the maximum close date, with the decision branch stated (E-01).
2. `agent_workflows/check_engine.py`: register `check.blocking-close-grandfathered` in `RULE_REGISTRY` at `info`/`ASSURANCE_REPOSITORY`/`DET_DETERMINISTIC`/`I-07`, with a comment recording why `info` and not `warning` (E-02).
3. Same file: a `grandfathered: bool = False` keyword-only arm of `check_release_gate_consistency` reporting the complement of the at-rest arm's candidate filter (pre-cutover plus undatable), deduplicated against the existing `seen_blocking_locations` (E-03).
4. `agent_workflows/cli.py`: a `--grandfathered` flag on `aw check`, threaded through `check_release_gates` into the new arm, modelled on `--strict-setid-length` and deliberately NOT overloading `--all` (E-04).
5. `tests/test_check_engine_release_gate.py`: new behavioral cases over `_create_minimal_repo` fixtures covering the six discriminating branches, plus an explicit `drift_exit_code == 0` assertion and a default-call regression case (E-05).
6. `AGENTS.md`: amend the release-gates paragraph to name the opt-in advisory surface and its `info`/no-exit-code limit, below the `<!-- /aw:block -->` marker (E-06).

## Deferred / out of scope (with reason)

- MOVING THE `release_gate_at_rest` CUTOVER so the population becomes reportable as errors. This is the single highest-leverage alternative and is deliberately refused: it converts 53 historical items into exit-blocking findings in one edit, and the remedy for most of them is a mutation `AGENTS.md` forbids. See F-04.
  - Carrier-Declined: A deliberate, permanent fence rather than an outstanding obligation. The cutover's registration comment states it records the feature introduction date, so there is no pending work here to lose track of; if a maintainer ever wants history judged as errors, the flag this plan adds shows them exactly what they would be signing up for first.
- THE PER-ITEM ADJUDICATION OF WHICH OF THE 53 ARE GENUINE GATE DROPS. Owned by pending plan `1hrlp3`, which ships a committed auditor and a `.findings.md` report with a three-value disposition per item. Re-deriving it here would duplicate a plan already written and would couple a check surface to an audit's conclusions. See F-07.
  - Carrier: mbjuv5
- BACKFILLING `- Close-Evidence:` ONTO HISTORICAL ITEMS so a legitimate evidence-based close becomes distinguishable (F-06). This would retire the upper-bound caveat, and it is exactly the forbidden mutation: the citation would be authored now, by an agent, for a close decision taken months ago by someone else, which forges an attestation.
  - Carrier-Declined: Permanently refused rather than deferred. `f7igdu` persists the citation going FORWARD, which is the only direction in which the evidence can be honest, so no future work is owed.
- WIDENING `release_gate_warnings` TO COVER SPEC CARRIERS. Noticed while reading that function (its comment records the plans-only asymmetry as deliberate and names it a separate behavior change). Unrelated to this plan's population and untouched.
  - Carrier-Declined: Already recorded as a deliberate choice in the code with its reasoning, and this plan neither depends on nor worsens it.

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is touched by a numbered E-item: `agent_workflows/check_engine.py` (E-02, E-03), `agent_workflows/cli.py` (E-04), `tests/test_check_engine_release_gate.py` (E-05), `AGENTS.md` (E-06). E-01 writes only to this plan's own `## Findings`, which needs no scope declaration.
- Under-scope: this plan makes the population REPORTABLE but changes no default, so a reader who never passes `--grandfathered` sees exactly what they see today. That is the intended outcome and not an omission: the alternative (reporting by default) is the CI-red blast radius the backlog item identifies as wrong. The consequence a reviewer should weigh is that visibility now depends on someone choosing to look, which is the same bargain `--strict-setid-length` already strikes. This plan also does NOT adjudicate the 53, so after it lands the population is reportable but not yet individually judged; that is `1hrlp3`'s job and the two are independent.

## Required tests / validation

Extend the EXISTING `tests/test_check_engine_release_gate.py` (40 test functions today) rather than adding a file, because its `_create_minimal_repo` builder and its five at-rest cases already stamp the exact `cutovers.release_gate_at_rest` knob these cases must move. One temp repo per case. Every assertion is an OUTCOME assertion on returned drift lists, rule ids, and exit codes; no test may read `check_engine.py` with `inspect`, `ast`, regex or substring search, assert a caller count, or pin a docstring or comment banner (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).

The six discriminating cases are the point: pre-cutover illegitimate close reported under the new rule with `grandfathered=True`; the same fixture silent under the default; post-cutover illegitimate close still under `check.blocking-item-closed-without-gate` and NOT under the new rule; undatable close in the new rule; ungated `done` item in neither; pre-cutover item with an executed same-gate carrier in neither. The exit-code property is asserted by calling `artifact_core.drift_exit_code` on the drift list, not by asserting a severity string.

MEASURE A BASELINE FIRST AND PASTE IT, before any edit, so a post-change failure is attributable to this plan rather than to another lane: bare `python3 -m pytest` per the execution contract (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; do not add `-n0`, a second `-q`, or `-p no:randomly`). The bar is NO NEW FAILURE against the executor's own measured baseline, plus the new cases.

Also run `aw check release-gates` (must still report `CONFORMS` with zero findings, which is the regression this plan most needs to not cause), then `aw check release-gates --grandfathered` (must report the population as `info` and still exit 0), and `aw check all` to confirm the full sweep is unchanged. Run `aw ipd lint` on this plan and `aw sanitize --agent` before treating any output as shareable.

A GREEN SUITE IS NOT ENOUGH HERE, and the gap is specific. The synthetic fixtures prove the arm partitions correctly at a cutover boundary; they say nothing about whether the LIVE population is what this plan claims. The load-bearing live evidence is V-01's re-measurement and V-04's two-command comparison showing the same tree reporting 0 findings without the flag and the full population with it, at the same HEAD. If the live count disagrees with `## Findings`, the `## Findings` numbers are the suspect ones (they came from throwaway scratch code) and the discrepancy must be resolved and recorded, not averaged away.

## Spec / documentation sync

NO `.spec.md` FILE IS AMENDED, and this is a verified finding rather than an omission. The close-legitimacy rule, the three legitimacy paths, and the LIVE-items-only scope live in `AGENTS.md`'s `## Release gates (Blocks-Release)` section and in `evaluate_blocking_close`'s own docstring, not in a spec. `- Scope-Paths:` therefore declares no `.spec.md`, and the run-end spec-edit reconciliation should report no declared and no actual spec edits.

ONE HONEST TENSION, RECORDED RATHER THAN PAPERED OVER. E-02 claims invariant `I-07` ("Release-gate preservation") in the draft invariant catalog spec `pqsx96`, whose control column already names `evaluate_blocking_close` plus `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch` and `check.orphaned-live-blocker`. This new rule belongs to the same invariant and the same family, so `I-07` is the correct home, but the catalog does not yet NAME it, exactly as `check.live-bug-ungated`'s registration comment records the same situation for itself and resolves it by PROPOSING the catalog edit rather than performing it out of scope. This plan does the same: the catalog addition is proposed here and deliberately not performed, since `pqsx96` is not in `- Scope-Paths:`.

`AGENTS.md` IS AMENDED (E-06), and the amendment is a factual correction plus a pointer to a new surface, not a contract change: the close-legitimacy rule, its three fixes, and the LIVE-items-only scope all keep their current meaning.

## Open questions

### OQ-01: Should the advisory also report the 7 carrier-present findings, given most of them look exonerated?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, REPORT ALL 53 AND CLASSIFY RATHER THAN FILTER. The temptation is to drop the 7 carrier-present findings (F-05) because inspection suggests most shipped under a superseded sibling. Rejected for two reasons. First, filtering would make this rule DISAGREE with `evaluate_blocking_close`, which is the single authority for legitimacy and whose `all(...)`-carriers behavior is a recorded maintainer ruling (2026-09-26); a check that silently second-guesses a ruled predicate is worse than one that reports a cohort a reader can dismiss. Second, the advisory is `info` and sets no exit code, so the cost of reporting a row a human then dismisses is one line of output, whereas the cost of hiding a genuine drop is a release shipping with an unlisted blocker. The classification in the detail text is what makes the cohort dismissible without hiding it.

### OQ-02: Should the flag also be available as a repository policy key, as `setids.strict` is for its sibling?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AS NO, SHIP THE FLAG WITHOUT A POLICY KEY, AND THE ASYMMETRY WITH `--strict-setid-length` IS THE REASON THE QUESTION IS WORTH STATING. That flag has a policy counterpart (`setids.strict`) because a repository may legitimately want history judged on EVERY run. Here the equivalent key would make the whole historical population appear as `info` findings on every `aw check` in this repository, which is noise rather than enforcement, and `info` cannot escalate into a gate however it is switched on. So the key would buy recurring output and no new enforcement, which is a bad trade. This is a DECISION, not a deferral, and it is deliberately NOT carried as a backlog item: an always-on view is a preference nobody has expressed, so filing it would assert an obligation that does not exist. The per-invocation flag is the smaller, reversible step, and if a maintainer later wants the always-on form the flag is what will have shown them its cost first.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the re-measurement transcript and the HEAD it ran at, showing all five numbers: the `done`+gated candidate count, the `legitimate=False`/`severity=error` count, the resolved `release_gate_at_rest` value, the maximum `_item_close_date` among the illegitimate set, and the count of those dated on/after the cutover. Paste the resulting `## Findings` row as committed. State explicitly which decision branch applies; if the maximum close date is no longer earlier than the cutover, paste the STOP and the raised question instead of proceeding.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the committed `RULE_REGISTRY` entry for `check.blocking-close-grandfathered` showing `info` severity and invariant `I-07`. Paste a transcript calling `artifact_core.drift_exit_code` on a drift list containing ONLY that rule and returning 0, which is the one claim the design rests on. Paste also the passing run of any existing registry-contract test in the suite (the tests importing `RULE_REGISTRY`, e.g. `tests/test_severity_tier_contract.py`) proving the new entry does not violate an existing severity-tier invariant.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the fixture test output proving the partition: the SAME pre-cutover fixture reported under `check.blocking-close-grandfathered` with `grandfathered=True` and reported by NOTHING under the default call; and a post-cutover fixture reported under `check.blocking-item-closed-without-gate` and NOT under the new rule. Paste the undatable-close case landing in the new rule. Paste evidence that no item is reported twice in one call (the dedup property), e.g. a fixture where both arms would otherwise match, asserting a single finding. Quote the committed detail string and confirm it states the item is grandfathered and does NOT recommend `aw backlog set done`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste BOTH commands run at the same HEAD on this repository: `aw check release-gates` (must print `CONFORMS` with 0 errors / 0 warnings / 0 info and exit 0) and `aw check release-gates --grandfathered` (must report the population as `info` findings and ALSO exit 0). Paste both exit codes explicitly via `echo $?`, since the equal-exit-code property is the point. Paste the committed `--grandfathered` help text and confirm it states the no-exit-code property. Confirm by inspection and state explicitly that `--all` / `include_retired` behavior was not altered, pasting an `aw check all` run for comparison.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the pre-change bare `python3 -m pytest` baseline summary line, then the post-change one, showing no new failure. Paste `python3 -m pytest tests/test_check_engine_release_gate.py` with its `N passed` line and the new test names, showing one case per discriminating branch (pre-cutover reported, same fixture silent by default, post-cutover unchanged, undatable, ungated, executed-carrier). Paste the `drift_exit_code` assertion's output. Confirm by inspection and state explicitly that no new test reads `check_engine.py` via `inspect`, `ast`, regex or substring search, and that none asserts this repository's live count of 53.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the amended `AGENTS.md` paragraph, plus the line number of `<!-- /aw:block -->` and of the edited paragraph, proving the edit is BELOW the marker. Paste `git diff AGENTS.md` showing that only the clause this plan owns changed and that no neighbouring sentence (from `b24o3q`, `2o5wka` or `47ttnv`) was reverted. Paste `git diff --cached --name-only` at commit time showing ONLY this plan's four declared paths, and confirm NO path under `.aw/records/backlog/` is modified or staged, which is the no-mutation property this plan's framing rests on. Paste `aw sanitize --agent` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the paths this plan declares, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. This repository is a SHARED CHECKOUT: before each commit run `git diff --cached --name-only` and unstage with `git restore --staged <path>` anything you did not change, and re-verify after any failed raw commit attempt, since a rejecting hook can leave foreign paths in the index.

THE ONE PROHIBITION THAT DEFINES THIS PLAN: do not modify, move, re-gate, re-open or re-close ANY file under `.aw/records/backlog/`, and do not change the `release_gate_at_rest` cutover in `.aw/config/project.json`. The first is forbidden by `AGENTS.md` (the gate rule governs LIVE items only; gating a closed item asserts a history that did not happen). The second would silently convert this plan's advisory population into 53 exit-blocking errors, which is the blast radius the whole design exists to avoid. A commit from this plan touching either is a failure of the plan even if every test passes. V-06 requires the staged-set evidence.

ORDERING NOTE: E-01 IS A GATE, NOT A FORMALITY. The premise this plan corrects was already invalidated once between the backlog item being filed and this plan being authored, so re-measure before writing code and take the STOP branch if the boundary has moved again.

POST-GATE LIFECYCLE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence. Perform the terminal transition with the tooled lifecycle (`aw ipd finalize`), never by hand-editing status or moving the file.
