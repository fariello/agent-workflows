# IPD: Give the release-gate close backstop an at-rest whole-tree arm with a stamped per-item cutover so a close that was never git-staged is still seen

- Date: 2026-09-30
- Kind: child
- Concern: THE DOCUMENTED BACKSTOP FOR A RELEASE-GATE BYPASS IS UNREACHABLE ONCE THE COMMIT LANDS, SO THE ONE SURFACE `AGENTS.md` CALLS "THE PORTABLE AUTHORITY" SEES NOTHING. `check_engine.check_release_gate_consistency`'s Rule 1 examines ONLY the paths `_staged_backlog_done_items` returns, which is `git diff --cached --name-status` over the backlog trees. `AGENTS.md` says of the opt-in hook that "the portable authority is the `aw check release-gates` rule family (`aw check` / `aw check all`) and CI, never the local hook alone", and CI runs `python -m agent_workflows check release-gates --agent` as a named fail-closed step in `tests.yml` on a FRESH `actions/checkout`, where the index is by definition empty. MEASURED at HEAD `7028ab5e`, driven end to end in a scratch repo: with a gated `done` item STAGED, `check_release_gate_consistency` returned `['check.blocking-item-closed-without-gate']`; after `git commit`, the staged set was empty and the SAME function returned `[]` while `evaluate_blocking_close` on the same file still returned `legitimate=False, severity='error'`. So the rule is not merely narrow, it is structurally blind on the exact surface that is supposed to be authoritative, and a bypass is invisible from the moment it is committed. On the live tree the gap is 49 real items: of 224 gated `done` items, 49 fail the shared predicate (46 with no same-gate carrier at all, 3 whose carriers are not executed), and `aw check release-gates` reports ZERO findings.
- Scope: IN: (1) a second AT-REST arm in `check_engine.check_release_gate_consistency` Rule 1 that walks every `done` backlog item on disk, judges it with the unmodified shared predicate, and reports `check.blocking-item-closed-without-gate`; (2) per-item grandfathering through the existing `config.resolve_cutover_date` mechanism under a new `release_gate_at_rest` feature key registered in `KNOWN_FEATURE_CUTOVERS`, so an item closed before this repository's boundary is never retroactively flagged; (3) keying the boundary on the item's CLOSE date (its newest `## Workflow history` record, via the shared `attention_contract.last_history_at`), not its filename date; (4) the shared carrier index rather than a per-item carrier scan, so the widened rule is O(corpus) and not O(items x corpus); (5) leaving `check_commit_invariants` commit-scoped so the opt-in local hook cannot refuse a commit over an unrelated item; (6) outcome tests; (7) the `AGENTS.md` and backlog README prose that currently assert the commit-scoped grandfathering rationale; (8) a CHANGELOG line. OUT: any mutation of a historical item (this plan reports, it never backfills); the 49-item audit itself (owned by backlog `mbjuv5`); the `HANDOFF` any-carrier-versus-all-carrier disagreement (pending plan `2o5wka`); the positional-spelling bypass (pending plan `47ttnv`); and the `SATISFIED` at-rest readability, which is child 01 and is this plan's dependency.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/config.py, AGENTS.md, .aw/records/backlog/README.md, tests/test_check_engine_release_gate.py, CHANGELOG.md
- Item-Dependencies: executed:f7igdu
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: nyzuyx
- Set: gateatrest
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: b24o3q

## Workflow history

- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `nyzuyx`, which asks whether the rule should widen. ANSWER: YES, and the reason is not that the rule is narrow but that its narrowness makes it structurally unreachable on the surface `AGENTS.md` names as authoritative (CI checks out fresh, so the index is empty). Measured at HEAD `7028ab5e`: 49 of 224 gated `done` items fail the shared predicate while `aw check release-gates` reports zero findings. The `nyzuyx` item's own stated worry (corpus-wide blast radius) is REAL and is answered by the existing per-item cutover mechanism plus a CLOSE-date key, measured to judge 9 items and flag 0 at a 2026-09-30 boundary. Ordered AFTER child 01 (`f7igdu`) because an at-rest arm that cannot see the `SATISFIED` route would report a legitimate evidence-satisfied close as an error.
- 2026-09-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `check.blocking-item-closed-without-gate` reachable where it is claimed to be authoritative, by adding an at-rest arm that judges every `done` backlog item on disk with the same shared predicate, grandfathered per item against a stamped cutover so the 49 historical violations are recorded as history rather than manufactured into a red build.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the boundary

- [ ] E-01 REGISTER THE CUTOVER FEATURE in `agent_workflows/config.py`'s `KNOWN_FEATURE_CUTOVERS` as `"release_gate_at_rest": "<the execution date, ISO>"`. The module's own block comment states the failure mode if this is skipped: "WHAT GOES WRONG IF YOU DO NOT REGISTER A FEATURE: `resolve_cutover_date` falls through to its tier-3 `None` ... the rule would ship as decoration." The value is the FEATURE INTRODUCTION date, never the enforcement boundary; `config.sync_cutovers_on_install` stamps the per-repo boundary from it, exactly as it does for the five features already registered (`spec_id6`, `dependency_schema`, `carrier_obligations`, `setid_length`, `prompt_id6`, `walkthrough_id6`). Do not invent a second mechanism and do not hardcode a calendar date in `check_engine`.
  - Depends on: none
  - Expected outcome: `config.resolve_cutover_date(repo, "release_gate_at_rest")` resolves in this repository after the next install/update stamp, and returns `None` (fail-open, everything grandfathered) in a repository that has never stamped it.
  - Execution state: pending

- [ ] E-02 ADD THE CLOSE-DATE HELPER that the boundary is keyed on, in `check_engine.py`, reusing the shared readers rather than writing a third history parser: bound the section with `attention._history_section_lines` and take the date with `attention_contract.last_history_at`, which `attention_contract`'s own docstring establishes as "the ONE RULE for which of these `## Workflow history` lines is the newest". Return a compact `YYYYMMDD` string for comparison against the resolved cutover, or `None` when the item has no parseable record. THE KEY IS THE CLOSE DATE, NOT THE FILENAME DATE, and this is the load-bearing choice of the plan: measured over the 224 gated `done` items, 208 were closed LATER than their filename date, and a filename-date boundary at 2026-09-30 would leave 9 items that were CLOSED after the boundary judged as pre-cutover. Filename date is the right key for `setid_length` (a naming rule about the name) and the wrong key here (a rule about an ACT). Treat a missing date as PRE-cutover, matching `config.SetidPolicy.applies_to_artifact_date`'s documented reasoning ("a missing date is its own defect owned by another rule, never a second consequence invented here").
  - Depends on: E-01
  - Expected outcome: a helper that returns `20260930` for an item whose newest history record is `- 2026-09-30 done (aw set): ...`, and `None` for an item with no history section; no new regex for either the section bound or the record grammar.
  - Execution state: pending

### Task group 2: the arm

- [ ] E-03 ADD THE AT-REST ARM to `check_engine.check_release_gate_consistency`, BESIDE Rule 1's staged arm and not replacing it. Walk `backlog._iter_items(repo_root)` (the shipped enumerator, which already covers both layouts and all five status dirs), keep the items whose parsed status is `done` and which carry `- Blocks-Release:`, skip any whose E-02 close date is before the resolved cutover (and skip ALL of them when the cutover resolves to `None`, which is fail-open by design), judge each with the UNMODIFIED `evaluate_blocking_close(repo_root, path, "done", item_text=text)`, and emit `check.blocking-item-closed-without-gate` for a verdict that is `not legitimate and severity == "error"`. DEDUPLICATE against the staged arm by location, so an item that is both staged and on disk yields ONE finding rather than two. Reuse the SAME rule id and the same `enrich_drift` shape; do NOT register a second rule, because it is the same invariant (I-07) observed at a different time, and a second id would double-count one defect and would silently fall through `_DEFAULT_RULESPEC`.
  - Depends on: E-02
  - Expected outcome: on a fixture repo with a committed (unstaged) gated `done` item dated after the cutover, `check_release_gate_consistency` reports exactly one `check.blocking-item-closed-without-gate`; with the item dated before the cutover, zero; with no cutover stamped, zero.
  - Execution state: pending

- [ ] E-04 MAKE THE ARM O(CORPUS), NOT O(ITEMS x CORPUS), by injecting the shared carrier index rather than letting each `evaluate_blocking_close` call re-walk both trees. `find_from_backlog_artifacts`'s docstring states the contract and the measurement ("673 per-item calls took 155 s against 259 ms for one shared index walk"), and `tests/test_carrier_scan_single_item_contract.py` MECHANICALLY REFUSES a call whose argument is a loop-derived variable, so a naive loop would not even land. MEASURED HERE, which is why this is its own item: the unmodified predicate called once per gated `done` item took 84.0 s on this corpus, while `_from_backlog_carrier_index` builds the identical mapping in 0.29 s and the same loop over the injected index takes 0.011 s, a total of 0.30 s, roughly 280x. Implement by giving `evaluate_blocking_close` an OPTIONAL keyword carrier-index parameter (default `None`, preserving every existing caller's behavior byte for byte) that the `HANDOFF` arm consults instead of calling the scanner; the four existing callers pass nothing and are unchanged. Do NOT add a process-lifetime cache: `find_from_backlog_artifacts`'s docstring records why ("A CACHED INDEX IS NOT THE FIX ... a process-lifetime cache here causes stale path lookups and falsely refuses valid closes").
  - Depends on: E-03
  - Expected outcome: the widened rule's wall time on the live tree is within a small multiple of the pre-change `check_release_gate_consistency` cost (measured baseline 0.34 s, and `aw check release-gates` 1.08 s), not the 84 s a per-item scan would cost; the single-item contract test still passes.
  - Execution state: pending

- [ ] E-05 PIN THE COMMIT-SCOPED BOUNDARY THAT MUST NOT MOVE. `check_engine.check_commit_invariants` composes `check_release_gate_consistency`, and its own comment states why it must stay commit-scoped: "Whole-tree release-gate rules are DELIBERATELY *NOT* added inside `check_commit_invariants`: that function is composed by the opt-in pre-commit aggregator and must remain commit-scoped so a local hook cannot refuse a commit over an unrelated artifact in a shared checkout." `AGENTS.md` states the same shared-checkout constraint independently. Since E-03 widens the function the aggregator composes, that guarantee would silently break. Add the at-rest arm behind an explicit keyword parameter (for example `at_rest=True` by default) and have `check_commit_invariants` call it with the at-rest arm DISABLED, then add a test that a committed (unstaged) pre-existing violation produces a finding from `check_release_gates` and NO finding from `check_commit_invariants`. The opt-in hook `hooks.backlog_blocking_close_gate` calls `check_release_gate_consistency` DIRECTLY, not through the aggregator, so it must be given the same disabled call; state that explicitly rather than leaving it to inference, because otherwise this widening turns a local pre-commit hook into a gate that refuses every commit in a repository carrying one historical violation.
  - Depends on: E-04
  - Expected outcome: a committed unstaged violation is reported by `check_release_gates` and is NOT reported by `check_commit_invariants` or by `hooks.backlog_blocking_close_gate.check`; a STAGED violation is still reported by all three.
  - Execution state: pending

### Task group 3: proof, prose, record

- [ ] E-06 WRITE THE BEHAVIORAL TESTS in `tests/test_check_engine_release_gate.py`, in the fixture-driven style the file already uses (`test_rule_blocking_item_closed_without_gate_reachable` and its two siblings build a temp repo, `git add`, and assert on the returned rule ids). Six cases, the first written FIRST and demonstrated FAILING: (a) a COMMITTED, unstaged gated `done` item with no carrier, dated after the stamped cutover, yields `check.blocking-item-closed-without-gate` from `check_engine.check_release_gates` (this is F-01 turned into a regression, and it is red at HEAD); (b) the same item dated BEFORE the cutover yields nothing; (c) the same item in a repo with NO stamped cutover yields nothing (fail-open); (d) the same item whose gate is handed off to an EXECUTED same-gate carrier yields nothing; (e) the E-05 boundary: that same committed item yields nothing from `check_commit_invariants` while still yielding a finding from `check_release_gates`; (f) an item both STAGED and on disk yields exactly ONE finding, not two. Every case asserts on returned rule ids and counts, never on source text (`AGENTS.md`; GUIDING_PRINCIPLES P16).
  - Depends on: E-05
  - Expected outcome: six new passing cases, with (a) shown failing before E-03 lands.
  - Execution state: pending

- [ ] E-07 CORRECT THE PROSE THAT NOW ASSERTS THE OLD SCOPE, in the two places that state it as a property rather than as an implementation detail. (1) `AGENTS.md`'s "Release gates" section says the opt-in hook "catches the hand-edit bypass (staging a done+blocking item directly ...)" and that "the portable authority is the `aw check release-gates` rule family ... and CI": that second clause was ASPIRATIONAL and is what this plan makes true, so say what the rule now examines (every `done` item on disk, grandfathered per item against the stamped cutover) and keep the honest limit about the local hook. (2) `.aw/records/backlog/README.md` points at `AGENTS.md` for the policy and needs at most a pointer, not a restatement; check before editing and leave it alone if it already only points. CRITICAL PLACEMENT CONSTRAINT: the `AGENTS.md` "Release gates" section is BELOW `<!-- /aw:block -->` and so is repo-local, editable text, while everything ABOVE that marker is installed from `agent_workflows/engine.py` and must NOT be hand-edited; paste the line numbers proving the edit is below the marker. ALSO check for a co-edit collision before writing: pending plans `2o5wka` and `47ttnv` both declare `AGENTS.md` in their scope and both touch this same paragraph, so state which of them has landed and edit only the sentence this plan owns.
  - Depends on: E-06
  - Expected outcome: the `AGENTS.md` release-gates paragraph describes the rule's actual scope and its grandfathering; no line above `<!-- /aw:block -->` is touched; no other plan's co-edit is reverted.
  - Execution state: pending

- [ ] E-08 RECORD THE CHANGE AND RE-MEASURE THE CORPUS. One `CHANGELOG.md` line under the pending 2.0.0 entry saying the release-gate check now sees a release-blocking item closed without a preserved gate even when the close was already committed, with items closed before the repository's cutover left as history. No em or en dashes. Then re-run the corpus census on the changed tree and report, as part of this item's own output: how many gated `done` items exist, how many fail the predicate, how many are judged by the stamped cutover, and how many findings `aw check release-gates` actually emits. If that last number is NOT zero, STOP and report rather than shipping: a nonzero count would red `main`, and the remedy is a maintainer decision about the boundary, not a quiet adjustment.
  - Depends on: E-07
  - Expected outcome: one CHANGELOG line, plus a pasted post-change census showing `aw check release-gates` still reporting zero findings on the live tree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PREDICATE IS SINGLE-SOURCED AND THIS PLAN MUST NOT FORK IT. `check_engine.evaluate_blocking_close` backs `backlog.run_set`, `set_records.close_on_answer`, this rule, and the opt-in hook; `AGENTS.md` states that is why "they cannot diverge". E-03 adds a CALLER, never a second judgement.
- THE CUTOVER MECHANISM IS ESTABLISHED AND HAS ONE HOME. `config.KNOWN_FEATURE_CUTOVERS` plus `config.resolve_cutover_date` (three tiers: `project.json` `cutovers.<feature>`, then the install history, then fail-open `None`) plus `config.sync_cutovers_on_install`. Six features already use it. Its block comment says explicitly: "TO ADD A FEATURE: put its introduction date here, and let `sync_cutovers_on_install` stamp the per-repo boundary. Do not invent a second mechanism."
- GRANDFATHERING IS PER ARTIFACT AND FAIL-OPEN, AND `check_setid_length` IS THE WORKED PRECEDENT. Its docstring: "an artifact dated before this repository's `cutovers.setid_length` boundary yields NOTHING, and a repository with NO boundary (the resolver's documented tier-3 `None`) yields nothing at all."
- A CARRIER LOOKUP IN A LOOP IS A MEASURED DEFECT WITH A MECHANICAL GUARD. `find_from_backlog_artifacts` is SINGLE-ITEM ONLY; `_from_backlog_carrier_index` is the shared walk; `tests/test_carrier_scan_single_item_contract.py` fails the build if a call site passes a loop-derived variable. `check_live_bug_gate` shows the right shape: it builds the index LAZILY, only when a candidate is found, "so a clean tree never pays for the walk".
- `check_commit_invariants` MUST STAY COMMIT-SCOPED, stated in its own comment and independently in `AGENTS.md`'s shared-checkout rule. This is what makes E-05 a required item rather than a nicety.
- SEVERITY IS LOAD-BEARING, AND `warning` IS NOT A SOFTER `error`. `artifact_core.drift_exit_code` exempts ONLY `info`, so a `warning` fails the gate exactly as an `error` does; `check.live-bug-ungated`'s registration comment records that a rule left permanently at `warning` is a recorded failure mode here. So this plan does NOT soften the rule to `warning` as a way of managing blast radius; the cutover is the instrument for that.
- CI RUNS THE FAMILY FAIL-CLOSED on a fresh checkout: `tests.yml` has a named step `aw check release-gates (release-gate family; fail closed)` running `python -m agent_workflows check release-gates --agent`. That step is both why the widening matters and why E-08's zero-findings re-measurement is a stop condition.

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | HIGH | THE RULE IS STRUCTURALLY BLIND ON THE SURFACE THAT IS CLAIMED TO BE AUTHORITATIVE. Driven at HEAD `7028ab5e` in a scratch repo: with a gated `done` item staged, `check_release_gate_consistency` returned `['check.blocking-item-closed-without-gate']`; after `git commit` the staged set was empty, the same call returned `[]`, and `evaluate_blocking_close` on the same file still returned `legitimate=False, severity='error'`. CI checks out fresh, so the index is always empty there. | The two rule-id lists and the verdict tuple, pasted at authoring. |
| F-02 | HIGH | THE LIVE CORPUS CARRIES 49 UNSEEN VIOLATIONS. Of 420 `done` items, 224 carry `- Blocks-Release:`; judged by the shared predicate, 175 are legitimate (all via `HANDOFF`) and 49 are not: 46 have no same-gate carrier at all and 3 have carriers that are not executed. `aw check release-gates` on the same tree reports ZERO findings. | The per-item census and the `check release-gates` output. |
| F-03 | HIGH | THE CLOSE DATE, NOT THE FILENAME DATE, IS THE CORRECT CUTOVER KEY, and this is measured rather than argued. Of the 224 gated `done` items, 208 were closed later than their filename date. At a 2026-09-30 boundary a filename-date key judges 0 items while a close-date key judges 9, so the filename key would leave a 9-item hole on day one and would keep widening. The 49-item illegitimate population has a newest CLOSE date of 2026-09-26 and a newest FILENAME date of 2026-09-25, so BOTH keys grandfather all 49 at a 2026-09-30 boundary; the difference is entirely about the items closed FORWARD. | The two census columns, pasted in V-02. |
| F-04 | MEDIUM | THE NAIVE IMPLEMENTATION IS 280x TOO SLOW AND WOULD ALSO BE REFUSED BY A SHIPPED GUARD. Measured on this corpus: 224 unmodified `evaluate_blocking_close` calls took 84.0 s, because each re-walks the plans and specs trees; `_from_backlog_carrier_index` produces the identical mapping in 0.29 s and the injected loop costs 0.011 s. `aw check release-gates` currently costs 1.08 s and `check_release_gate_consistency` 0.34 s, so a per-item scan would make a command a human waits on roughly 80x slower. `tests/test_carrier_scan_single_item_contract.py` would additionally refuse the loop outright. | The three timings and the contract test's stated purpose. |
| F-05 | MEDIUM | WIDENING THE SHARED FUNCTION SILENTLY WIDENS THE OPT-IN PRE-COMMIT HOOK AND THE COMMIT AGGREGATOR, both of which call it. Without E-05, a repository carrying ONE historical violation would have every commit refused by `hooks.backlog_blocking_close_gate` over an artifact the committer never touched, which is exactly what `check_commit_invariants`'s own comment and `AGENTS.md`'s shared-checkout rule forbid. | `hooks/backlog_blocking_close_gate.check` calling `check_release_gate_consistency` directly, and the aggregator's comment. |
| F-06 | MEDIUM | THE `SATISFIED` ROUTE IS INVISIBLE AT REST, WHICH IS WHY THIS PLAN IS ORDERED SECOND. The predicate's `SATISFIED` arm reads only the transient `--evidence` argument, so an at-rest arm shipped alone would report every legitimate evidence-satisfied close as an error. Child 01 (`f7igdu`) records the citation durably; this plan declares `executed:f7igdu` as its dependency. Measured mitigation: the corpus contains ZERO `SATISFIED` closes today, so the false-positive population is currently empty and the dependency is about FORWARD correctness. | The verdict-path census (`HANDOFF` 175, `SATISFIED` 0, illegitimate 49) and child 01's concern statement. |
| F-07 | LOW | THE STAGED ARM MUST BE KEPT, not replaced. It reads the STAGED BLOB (`_blob_text(repo_root, ":0:", staged_path)`), so it judges the content being committed even when the working tree differs, and it catches a violation at the moment a local hook can still refuse it. The at-rest arm reads the file on disk. They answer different questions at different times, which is also why E-03 must deduplicate by location. | `_staged_backlog_done_items` and the `:0:` blob read in Rule 1. |
| F-08 | LOW | `_backlog_done_dirs` IS DEAD CODE sitting directly above the staged helper, with no caller anywhere in the package. It looks like the beginning of exactly the at-rest walk this plan adds. Deliberately NOT touched: it is out of the declared scope's intent and deleting it is a separate tidy-up. Named so a reviewer does not read it as the intended seam. | A package-wide grep returning only its own definition. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/config.py`: register `release_gate_at_rest` in `KNOWN_FEATURE_CUTOVERS` (E-01).
2. `agent_workflows/check_engine.py`: add the close-date helper over the shared history readers (E-02).
3. `agent_workflows/check_engine.py`: add the at-rest arm to Rule 1, cutover-gated and deduplicated (E-03).
4. `agent_workflows/check_engine.py`: give `evaluate_blocking_close` an optional carrier-index parameter and use it from the arm (E-04).
5. `agent_workflows/check_engine.py`: keep the commit aggregator and the opt-in hook commit-scoped via an explicit parameter (E-05).
6. `tests/test_check_engine_release_gate.py`: six behavioral cases, the first written failing (E-06).
7. `AGENTS.md` (below the managed-block marker) and, if needed, `.aw/records/backlog/README.md`: correct the scope prose (E-07).
8. `CHANGELOG.md`: one line, plus the post-change corpus census as this item's own output (E-08).

## Deferred / out of scope (with reason)

- MUTATING ANY HISTORICAL ITEM. This plan REPORTS; it never backfills a gate, a citation, or a carrier onto a closed item. `AGENTS.md` states the release-gate rule governs LIVE items only and that writing a gate onto a closed item "would assert a history that did not happen". The cutover is what makes reporting-without-mutating viable.
  - Carrier-Declined: Nothing is owed, because the mutation is FORBIDDEN rather than unfinished. `AGENTS.md` rules that writing a gate onto a closed item asserts a history that did not happen, so filing a carrier would assert pending work for something we have decided must never be done. The historical population is separately owned as an AUDIT (the next row), which reports rather than rewrites.
- THE 49-ITEM AUDIT. Already filed as backlog `mbjuv5` ("Audit items already closed done through the ungated positional aw backlog set spelling"), whose own text anticipates this exact plan: "the rule is STAGED-PATH scoped in the commit-invariants caller and whole-tree scoped in the sweep, and those two scopes see different populations". Note that `mbjuv5` measured the population as possibly empty; this plan measures it at 49 and that number should be handed to it.
  - Carrier: mbjuv5
- THE `HANDOFF` ANY-CARRIER VERSUS ALL-CARRIER DISAGREEMENT (pending plan `2o5wka`, backlog `lsbd32`). Measured for the record because the two plans interact: 4 of the 175 `HANDOFF`-legitimate historical closes have at least one unexecuted same-gate carrier, so if `2o5wka` lands the illegitimate population becomes 53 rather than 49. All 4 were closed on or before 2026-09-07, so the cutover grandfathers them either way and the interaction is not a blocker.
  - Carrier: lsbd32
- THE POSITIONAL-SPELLING BYPASS (pending plan `47ttnv`, backlog `mawwlc`). That plan makes the ungated spelling call the predicate; this one makes the resulting state visible afterwards. They are complementary and neither depends on the other.
  - Carrier: mawwlc
- CHANGING THE RULE'S SEVERITY OR ITS REGISTERED INVARIANT. It stays `error` under I-07. Softening to `warning` would buy nothing (`drift_exit_code` exempts only `info`) and would weaken a stated contract.
  - Carrier-Declined: There is no defect to carry. The current severity and invariant are correct and this row records a change we are deliberately NOT making; `check.live-bug-ungated`'s registration comment already records why a permanent `warning` is a failure mode here, so a carrier would assert outstanding work against a settled decision.
- DELETING THE DEAD `_backlog_done_dirs` HELPER (F-08). Out of the declared intent; a separate tidy-up.
  - Carrier: y2vnr7
- AMENDING THE INVARIANT-CATALOG SPEC. See the spec-sync section: `pqsx96` is `draft` and describes I-07's controls generically. Raised as OQ-02, not performed.
  - Carrier-Declined: Nothing is owed TODAY, and OQ-02 records the trigger for when it would be. Nothing in `pqsx96`'s I-07 row becomes false when this plan lands (its honest-limits column speaks about the local hook's reach, not the check's temporal scope), so there is no defect to hand on; and the spec is `- Status: draft` and actively being authored, so filing a carrier against it now would queue an edit that would collide with its author. The trigger is stated in OQ-02: file one only if the maintainer wants the row to state the scope explicitly, once `pqsx96` settles.

## Scope check

- Over-scope: none. Each declared path is touched by named items: `config.py` by E-01; `check_engine.py` by E-02 through E-05; `tests/test_check_engine_release_gate.py` by E-06; `AGENTS.md` and the backlog README by E-07; `CHANGELOG.md` by E-08.
- Under-scope: checked rather than assumed. A package-wide grep for the rule id and for `check_release_gate_consistency` found exactly these consumers: `check_engine.check_release_gates` (the named target and the full sweep), `check_engine.check_commit_invariants` (the commit aggregator, handled by E-05), `hooks/backlog_blocking_close_gate` (the opt-in hook, also handled by E-05), `hooks/precommit_scope_gate` (which goes through the aggregator and so inherits E-05), `cli._run_check` (the `release-gates` target, which needs no change), `production_checks.backlog_cross_tree` (which calls `check_release_gates` and filters to the item and its produced paths, so the widening cannot make it report an unrelated item), and `run_evidence.RUN_FINDING_CODES` (a predicate NAME in a documentation row, no behavior). `agent_workflows/engine.py` carries no copy of this policy prose (grepped), so the managed-block template needs no edit.

## Required tests / validation

`python3 -m pytest` bare, plus `python3 -m pytest tests/test_check_engine_release_gate.py tests/test_carrier_scan_single_item_contract.py tests/test_config.py -o addopts=""` for the per-test counts of the three files this plan's changes bear on. Plus, on the live tree: `aw check release-gates --agent` (must report ZERO findings, which is E-08's stop condition), `aw check all --agent` (finding count must equal the pre-change baseline, both pasted), and a timing comparison of `check_release_gate_consistency` before and after. Plus `aw ipd lint --phase pre-transition` on this plan before any terminal move.

## Spec / documentation sync

- `AGENTS.md` is edited by E-07 and is declared in `- Scope-Paths:`. The edit is BELOW `<!-- /aw:block -->`, in the repo-local "Release gates (Blocks-Release)" section; nothing in a managed block is touched.
- NO `.spec.md` IS AMENDED, and the judgement is recorded rather than assumed. The invariant-catalog spec `pqsx96` row I-07 names this rule among I-07's controls and states its honest limits in terms of the LOCAL HOOK, not in terms of the check's scope, so the row remains accurate after this plan. `pqsx96` is `- Status: draft` and actively being authored, so amending it would collide with its author. Raised as OQ-02.
- `.aw/records/backlog/README.md` is declared because E-07 inspects it; if it turns out to only POINT at `AGENTS.md` for the policy (which a read at authoring suggests), E-07 leaves it unchanged and V-07 says so. Declaring a path the plan may not modify is the safe direction: the finalize scope gate reconciles what was changed against what was declared, and an undeclared edit is the failure it catches.

## Open questions

### OQ-01: Should the boundary be the item's close date or the repository's install stamp alone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: BOTH, composed, which is what the shipped mechanism already does and is why no new machinery is needed. The REPOSITORY boundary comes from `config.resolve_cutover_date` (stamped per repo, fail-open `None`); the PER-ITEM date compared against it is the close date (E-02). `config.SetidPolicy.applies_to_artifact_date` is the exact precedent for that composition. Resolved from repository evidence, and the per-item key was chosen on measurement (F-03): 208 of 224 items were closed later than their filename date, so a filename key leaves a hole that grows.

### OQ-02: Should the invariant-catalog spec `pqsx96` row I-07 be amended to state the rule's scope?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, not silently skipped, and the reason is ownership rather than effort. `pqsx96` is `- Status: draft` and its I-07 row describes the CONTROLS generically; its honest-limits column speaks about the local hook's reach, not about the check's temporal scope, so nothing in it becomes false when this plan lands. Editing a draft spec another agent is authoring is the collision `AGENTS.md`'s shared-checkout rule warns about. If the maintainer wants the row to state the scope explicitly, that is a one-line amendment to file as its own item once `pqsx96` settles. Raised so the omission is a recorded decision and not an oversight.
- Carrier-Declined: Nothing is owed TODAY, and the TRIGGER for owing it is stated rather than left vague. No claim in `pqsx96`'s I-07 row becomes false when this plan lands, so there is no defect to hand on; and the spec is `draft` and under active authorship, so filing a carrier now would queue an edit that collides with its author. FILE ONE only if the maintainer decides the row must state the check's temporal scope explicitly, and only once `pqsx96` reaches a settled status. That decision is a maintainer judgement about spec wording, which is exactly the class of question this section is meant to surface rather than resolve.

### OQ-03: What should happen if the post-change census shows a nonzero finding count on the live tree?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: STOP AND REPORT, never adjust the boundary quietly. E-08 makes this a stop condition because `aw check release-gates` is a fail-closed CI step, so a nonzero count reds `main`. Measured at authoring, a close-date boundary at 2026-09-30 judges 9 items and flags 0, and the illegitimate population's newest close date is 2026-09-26, so the expected outcome is zero; a nonzero result would mean either the boundary resolved differently than expected or a new violation landed between authoring and execution, and both are maintainer decisions about the boundary rather than implementation choices. This mirrors the same stop condition pending plan `2o5wka` E-08 sets for its own re-measurement.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the added `KNOWN_FEATURE_CUTOVERS` entry with its value, and paste `config.resolve_cutover_date(<this repo>, "release_gate_at_rest")` BEFORE and AFTER whatever stamps it, showing the tier it resolved through. ALSO paste the same call against a temp repo that has never stamped it, returning `None`, proving the fail-open tier is reachable. State plainly whether this repository's `.aw/config/project.json` `cutovers` block gained the key during execution and by what mechanism; if it did not, say so and explain what a consumer sees (the answer must be "everything grandfathered", not "undefined").
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the helper's return for three fixture items: one whose newest history record is dated, one with several records out of order (proving `last_history_at` and not a fresh parser decides which is newest), and one with no history section (returning `None`). Then paste the RE-MEASURED corpus census that F-03 rests on, at execution HEAD: the count of gated `done` items, how many were closed later than their filename date, and how many each key judges at the stamped boundary. Confirm no new regex for the history section bound or the record grammar was added, by naming the two shared functions called.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, for a fixture repo, the returned rule-id lists for four states: committed-unstaged violation dated after the cutover (exactly one finding); the same dated before (zero); the same with no cutover stamped (zero); and the same item ALSO staged (exactly ONE finding, proving deduplication and not two). For the last, paste the count, not just the presence. State which rule id was emitted and confirm no new rule id was registered, by pasting `check_engine.RELEASE_GATE_RULES` unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste wall-clock timings from the live tree for `check_engine.check_release_gate_consistency` and `aw check release-gates`, BEFORE the change and AFTER, on the same machine in the same session. The authoring baselines were 0.34 s and 1.08 s; the after numbers must be the same order of magnitude and must NOT approach the 84.0 s a per-item carrier scan costs. Paste the 84.0 s naive measurement too (or re-derive it), so the comparison is a demonstrated delta rather than an assertion. Paste `python3 -m pytest tests/test_carrier_scan_single_item_contract.py -o addopts=""` passing, proving the loop-derived-argument guard is satisfied. Confirm by pasting the call sites that the four pre-existing `evaluate_blocking_close` callers pass no carrier index and are unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste, for ONE fixture repo carrying a committed unstaged violation, all three results side by side: `check_release_gates` (finding present), `check_commit_invariants` (finding ABSENT), and `hooks.backlog_blocking_close_gate.check` (exit 0, no message). Then paste the STAGED variant of the same fixture showing all three reporting it. A pasted pass that omits the hook FAILS this item: the hook calls the widened function directly, so it is the surface most likely to regress into refusing unrelated commits.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste case (a) FAILING at HEAD before E-03 is applied, with its assertion error, then passing after. Paste `python3 -m pytest tests/test_check_engine_release_gate.py -o addopts=""` with per-test counts, and the bare `python3 -m pytest` summary line. Confirm each new case asserts on rule ids, counts, or exit codes and reads no production source text.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the rewritten `AGENTS.md` paragraph verbatim, and paste the line number of `<!-- /aw:block -->` together with the line numbers of the edited lines, proving the edit is below the marker. Paste `git diff --stat` showing `agent_workflows/engine.py` ABSENT, and paste the grep that justified excluding it. State whether `2o5wka` or `47ttnv` has landed its own edit to this paragraph and confirm neither was reverted or rewritten; a diff that undoes another plan's sentence FAILS this item. For the backlog README, state explicitly whether it was changed and why. Confirm no em or en dashes in the user-facing prose.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the CHANGELOG line, then the post-change census on the live tree: gated `done` count, predicate-failing count, cutover-judged count, and the FULL `aw check release-gates --agent` output. That last must report zero findings; if it does not, this item FAILS and the plan stops for a maintainer decision rather than adjusting the boundary. ALSO paste `aw check all --agent` before and after with its finding count, proving the widening added no finding elsewhere, and `aw sanitize --agent` clean over the changed paths. Finally paste `git diff --cached --name-only`, which must be a subset of the six declared scope paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING, stated plainly because this is a policy change and the backlog item that asked for it flagged the blast radius itself. The `aw check` rule that is supposed to catch a release-gate bypass currently cannot see one after the commit lands, which means it cannot see one in CI at all. This plan makes it see every `done` backlog item on disk, judged by the same predicate that already governs the close, and grandfathers every item closed before this repository's stamped boundary so no historical close is retroactively flagged. Measured consequence on this tree: 49 items fail the predicate and ALL 49 are grandfathered by their close date, so the expected finding count after the change is zero and E-08 makes a nonzero count a stop condition rather than a thing to work around.

TWO THINGS THE APPROVAL ALSO COVERS, because neither is implied by the title. FIRST, the opt-in local pre-commit hook and the commit-invariant aggregator both call the function being widened, so without E-05 this change would make a local hook refuse commits over artifacts the committer never touched; E-05 keeps them commit-scoped and V-05 proves it on the hook specifically. SECOND, the widened arm is O(corpus) by construction: the naive per-item form was measured at 84.0 s against 0.30 s for the shared index, on a command a human waits on.

WHAT THIS PLAN DELIBERATELY DOES NOT DO. It does not mutate a single historical record, it does not audit the 49 (backlog `mbjuv5` owns that and should be handed the number), it does not change the rule's severity or invariant, and it does not touch the two adjacent defects already owned by pending plans `2o5wka` and `47ttnv`.

EXECUTION CONTRACT. This plan declares `- Item-Dependencies: executed:f7igdu` and must not execute before child 01 has executed: an at-rest arm shipped alone reports a legitimate evidence-satisfied close as an error. Commit only the declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Paste actual runner output for every test claim. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence, including the zero-findings census. On completion, move the plan to `.aw/records/plans/executed/` through the lifecycle tooling, not by hand.
