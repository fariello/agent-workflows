# IPD: Default Blocks-Release on a bug at creation and preserve it through graduation

- Date: 2026-09-11
- Kind: child
- Concern: A bug item gets a release gate only if its author remembers to pass one, and measurably they do not. RE-MEASURED AT REVIEW (2026-09-12, HEAD `165e35e8`): 196 items, 112 `Work-Kind: bug`, 68 live (`open`/`blocked`/`graduated`), of which 22 carry no `- Blocks-Release:` (10 `open`, 11 `graduated`, 1 `blocked`); the authored figure of 28 of 60 is historical. The graduation leak reproduces EXACTLY: all 11 graduated gateless bugs have a `- From-Backlog:` carrier, 13 carriers in total, and 0 of the 13 carries a gate.
- Scope: Make the correct gate the DEFAULT rather than an act of memory, at both points where it is currently lost: creating a bug item, and graduating one into a plan or spec. Does NOT enforce anything retroactively (child 03 owns the backfill and the checker), does NOT gate other work kinds, and does NOT change what `next` resolves to.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/cli.py, tests/test_bug_gate_default.py
- Item-Dependencies: executed:zqs0px
- Status: approved
- Readiness: go-pending-approval
- Set: nobugship
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: di08i9
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-09-18 executed-work-performed (opencode its_direct/pt3-claude-opus-5-1m-us): all four `E-*` items PERFORMED and all four `V-*` items `pass` with pasted evidence; `aw ipd lint --phase pre-transition` CONFORMING. The TERMINAL TRANSITION IS DELIBERATELY NOT TAKEN HERE: this ran as a managed lane worker, and `aw ipd finalize` refused with `AW-LIFECYCLE-ROLE-001` ("the runner owns begin/finalize for managed lanes; a worker-role process must not run them"), so the plan stays in `pending/` with `- Status: approved` for the driver to transition. Suite: `8096 passed, 3 skipped, 2 xfailed` against a pre-edit baseline of `8076 passed, 3 skipped, 2 xfailed` (+20 = exactly the tests added; empty failure-set delta). Blast radius `97 passed`, identical to baseline, no fixture modified. `check_release_gate_consistency` unchanged at its 2 pre-existing findings.
  TWO DEPARTURES FROM THE PLAN AS WRITTEN, both recorded with evidence rather than taken silently. FIRST, E-02 was IMPLEMENTED, not deferred: `b5sfwm` has executed since review and `aw backlog set` now carries `--work-kind`, so the deferral's sole stated premise is false and the E-item's own conditional prescribes the implementation branch; the default now fires on BOTH dispatch paths (decision D1). SECOND, V-03's provenance measurement INVERTED review's conclusion: 180 `From-Backlog` carriers now exist, 103 of them acquired the field after the first commit, so the setter route E-03 covers is the MAJORITY rather than 1 of 13 (decision D5). The uncovered hand-authoring population (77) and the `aw specs set` gap are unchanged and carried.
  SCOPE DELTA REQUIRING FINALIZE ARGUMENTS: `agent_workflows/status_set.py` was changed but is NOT declared (it is the write site E-02/E-03 explicitly cite), and the declared `agent_workflows/cli.py` was NOT modified (both flags were already registered there). The Scope check section carries the exact `--scope-reason` / `--scope-ack` pair to pass. THREE DEFECTS FILED, none of them this plan's own work: `4le6yz` (bug), `mod4ml` (chore), `4fe3al` (bug).
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (BLOCKER) through PR-010, all FIXED, none deferred, no open question left blocking; readiness `go-pending-approval`. Record: `.aw/records/reviews/20260911-nobugship-02-di08i9-default-blocks-release-on-a-bug-at-creation-and-preserve-it.review.md`. `aw ipd lint --phase author --agent` CONFORMING (clean, exit 0, 0 findings) before semantic review and `--phase review-finalize` after every revision. DISCLOSURE: the same agent/model family authored this Set, so treat this as a near-self-review; its value rests on what was EXECUTED, not on the reading.
  E-01 WAS IMPLEMENTED IN A THROWAWAY COPY AND IT BROKE THE SUITE, WHICH IS HOW THE BLOCKER WAS FOUND. Patching `backlog.run_new` exactly as E-01 prescribed (default `next` for a bug, REFUSE when it does not resolve) produced `10 failed, 77 passed` across `tests/test_backlog.py`, `tests/test_backlog_work_kind_rename.py`, `tests/test_backlog_blocking_close_gate.py` and `tests/test_release_gate_close.py`, every failure being a fixture that creates no release record. The cause is not the fixtures: `aw install` on a fresh repo creates NO `.aw/records/releases/` directory at all (driven at review on an empty repo), so the prescribed refusal would make `aw backlog new --work-kind bug` FAIL OUTRIGHT in every freshly installed adopter repo. Re-patched to fall back to ungated when `next` does not resolve, the bare suite passed `5971 passed, 3 skipped, 2 xfailed in 58.71s`. PR-001 rewrites E-01 accordingly and the refusal is kept where it belongs: on an EXPLICIT unresolvable `--blocks-release`, which already ships and must not regress.
  THE SECOND MEASURED COLLISION IS THAT THE DEFAULT MANUFACTURES AN IMMEDIATELY-ILLEGITIMATE ITEM. `aw backlog new --work-kind bug --status done` is legal today, and with the default applied it writes a `done` item carrying `Blocks-Release: next` with no handoff and no evidence. Driven through the CLI in a scratch repo with the patched code and then staged, the shipped `check_engine.check_release_gate_consistency` returned exactly one `check.blocking-item-closed-without-gate` (ERROR, exit-blocking). The setter is not the hole: `aw backlog set <path> --status done` on a gated item REFUSES with exit 1, verified. Creation is. PR-002 makes E-01 skip the default for `done`.
  THE GRADUATION HALF IS WEAKER THAN THE PLAN CLAIMS, measured by provenance rather than asserted: of the 13 `From-Backlog` carriers, 12 carry the field in the file's FIRST commit (hand-authored at scaffold time) and only 1 gained it later. `aw ipd scaffold` accepts no `--from-backlog` flag at all, so the setter route E-03 targets covers at most 1 of 13 historically. E-03 is still right to exist and it strictly REDUCES future mismatch, but the plan's framing of it as closing the leak was inflated; PR-004 states the residual and hands it to child 03 rather than widening this child.
  EIGHT THINGS WERE DRIVEN RATHER THAN RECALLED: the five population counts recomputed from disk; the graduation leak and its 13 carriers recomputed per-item with `check_engine.find_from_backlog_artifacts`; the carriers' git provenance traced to their first commit; `resolve_release(repo, 'next')` confirmed to return `f33nrj` (2.0.0); a fresh `aw install` inspected for a releases dir; the prescribed refusal and the fallback each patched in and the suite run against both; the `done` collision driven through the CLI and the shipped checker; and the setter's refusal on a gated close driven to exit 1.
- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the second third of the answer to the maintainer's 2026-09-11 question. MEASURED at HEAD `2ff2b1b1` (NOTE: review could not verify this commit; `git cat-file -t 2ff2b1b1` reports "Not a valid object name" in this repository, so the authored provenance anchor is unresolvable and the figures below were re-derived from disk instead): `backlog.run_new` reads `--blocks-release` from args and validates it resolves to a release record (`backlog.py:388-397`), but applies NOTHING when the flag is absent, so a `--work-kind bug` item is born ungated. `next` resolves to exactly one `planned` release (`f33nrj`, version 2.0.0, verified). THE GRADUATION LEAK IS THE HALF THAT WOULD OTHERWISE BE MISSED and it was found by measurement rather than reasoning: `AGENTS.md:38` already instructs an agent graduating an item to "inherit the item's `- Blocks-Release:` if it has one", yet all 11 graduated gateless bugs have a plan and none of those plans carries a gate. So the obligation exists in prose and is not honored, which is the same failure shape as the rule itself.

## Goal

Make a bug carry its release gate by construction at both points it is currently lost, so the rule holds without anyone remembering it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: default it at creation

- [x] E-01 DEFAULT THE GATE WHEN A NEW ITEM'S WORK-KIND IS `bug`, in `backlog.run_new`, where the flag is read today (`backlog.py:388-397`, re-verified at review). When `--blocks-release` is ABSENT and the work kind is `bug`, apply `next` and SAY SO in the command's output, so the author sees a field they did not type.
  DO NOT REFUSE WHEN `next` DOES NOT RESOLVE; FALL BACK TO UNGATED AND SAY SO. This REPLACES the plan's original instruction to refuse, which review implemented and measured as breaking (PR-001). Patching `run_new` to refuse produced `10 failed, 77 passed` across four existing test files, every failure a fixture that creates no release record; and the cause is not the fixtures, because a fresh `aw install` creates NO `.aw/records/releases/` directory at all (driven at review on an empty repo, then `--blocks-release next` refused with exit 2). A refusal would therefore make `aw backlog new --work-kind bug` fail outright in every freshly installed adopter repo, which is a far worse outcome than an ungated item that child 03's checker will report. Implement the resolution check BEFORE assigning the default (call `releases.resolve_release(repo_root, "next")` and only default when it returns a path), so the absent-release case takes the fallback and never reaches the explicit-value refusal below. Re-patched that way, the bare suite passed `5971 passed, 3 skipped, 2 xfailed` at review.
  KEEP REFUSING AN EXPLICIT UNRESOLVABLE VALUE. `--blocks-release next` in a repo with no planned release already exits 2 today (`backlog.py:391-397`) and `tests/test_backlog.py:254` pins it. The fallback above must apply ONLY to the ABSENT case; an explicit value the author typed and that does not resolve must still refuse, or that shipped contract regresses.
  SKIP THE DEFAULT WHEN `--status done`, because otherwise the tool writes an item the shipped checker immediately rejects (PR-002). `aw backlog new --work-kind bug --status done` is legal, and with the default applied review drove it through the CLI in a scratch repo, staged the result, and `check_engine.check_release_gate_consistency` returned exactly one `check.blocking-item-closed-without-gate` (ERROR, in the exit-blocking sweep). The setter is not the hole: `aw backlog set <path> --status done` on a gated item REFUSES with exit 1, verified, so creation would be the only route that manufactures the violation. Skip the default for `done` and report that it was skipped and why; also skip for `parked` for the same reason the attention view hides it, and record that choice.
  AN EXPLICIT `-` MUST STILL CLEAR IT. The author may deliberately file an ungated bug, and the flag already distinguishes an explicit `-` from an absent value (`br is not None and br != "-"`). Preserve that: a default is not a prohibition, and forcing a gate with no escape would make the tool unusable for the case where a bug genuinely does not gate the release.
  ANNOUNCE IT ON BOTH OUTPUT SURFACES, NOT ONLY THE HUMAN ONE. `run_new` has an `--agent`/`--json` branch that emits a `CommandResult` and returns before the human `sys.stdout.write` (`backlog.py:414-462`), so a notice written only to the human path is invisible to the runner that will most often call this. Carry the fact in the structured result (a `data` key stating the gate was defaulted, or a `Diagnostic` at `info` severity), and keep the human line too. State which mechanism you chose and why.
  - Depends on: none
  - Expected outcome: `aw backlog new --work-kind bug` with no gate flag produces an item carrying `- Blocks-Release: next` and reports the default on BOTH the human and the agent surface; `--blocks-release -` still produces an ungated item; an ABSENT flag with no resolvable `next` produces an UNGATED item and says so (no refusal, no dangling gate); an EXPLICIT unresolvable `--blocks-release` still exits 2; `--status done` is not defaulted.
  - Execution state: performed
  - Execution note: the decision was factored into ONE shared predicate, `backlog.decide_gate_default` (`backlog.py`), rather than written inline in `run_new`, because E-02 needs the identical decision at two further call sites and three copies would drift. The gating kind set is the module constant `GATE_DEFAULT_KINDS = frozenset({"bug"})` and the skip set is `_GATE_DEFAULT_SKIP_STATUSES = frozenset({"done", "parked"})`. `run_new` calls the predicate AFTER the existing explicit-value refusal, so the shipped exit-2 contract is untouched, and the predicate itself only ever RETURNS a value (it never refuses), which is what makes the absent-flag case fall back. Announced on both surfaces per OQ-01: the human `sys.stdout.write` on both the preview and applied paths, and on the structured path a `data` triple (`blocks_release`, `blocks_release_defaulted`, `blocks_release_default_notice`) plus an `Evidence` receipt. THE MECHANISM CHOICE IS RECORDED BECAUSE E-01 ASKED FOR IT: an `info` `Diagnostic` was REJECTED, because `to_agent_record` derives `findings` from `len(diagnostics)` irrespective of severity, so it would emit `findings: 1` on a successful filing; `data` alone was insufficient, because the COMPACT `--agent` record omits `data` entirely. `Evidence` is what survives into the compact record (`"evidence":["blocks-release-default:next"]`), so the pair covers both structured surfaces with `findings: 0`. Skipping `graduated`/`blocked` was considered and REJECTED (decision D3): both are LIVE statuses the rule requires to carry the gate, and 11 of the 22 measured gateless bugs were `graduated`.

- [x] E-02 DEFAULT IT ON A WORK-KIND CHANGE TOO, so the gate follows a reclassification. `aw backlog set` gains work-kind and priority setters in plan `b5sfwm`; when an item's work kind BECOMES `bug` and it carries no gate, apply the same default and report it.
  `b5sfwm` HAS NOT LANDED, VERIFIED AT REVIEW, SO THE DEFERRAL IS THE EXPECTED OUTCOME RATHER THAN THE EXCEPTION. Its `- Status:` is `reviewed` with `- Readiness: go-pending-approval`, it sits in `pending/`, and `aw backlog set --help` lists neither `--work-kind` nor `--priority` (driven at review; the flag list is `--status --message --gate-kind --gate-ref --blocks-release --evidence --dry-run --yes --commit/--no-commit`). So unless `b5sfwm` executes first, there is NO flag on this verb for a reclassification to arrive through, and this E-item's deliverable is the RECORDED DEFERRAL, not code. Do NOT add a work-kind setter here to make the default reachable: that would duplicate `b5sfwm`'s entire scope, and it would land in a second place from the one that plan is reviewed to change.
  NOTE THE TWO-DISPATCH-PATH TRAP FOR WHOEVER LANDS THIS LATER (measured at review, and it is why the deferral is cheap but the implementation is not). `aw backlog set` forks on whether `--status` was PASSED (`cli.py:11270-11286`): the positional spelling routes to `status_set.run_set_command(..., scoped_type="backlog")`, whose Work-Kind and Blocks-Release writes are already hoisted out of every status branch (`status_set.py:706-773`), while the `--status` spelling routes to `backlog.run_set`, which applies its gate write post-render (`backlog.py:560-571`). A default wired into one path only would fire for one spelling and not the other, which is worse than not shipping it, because it would teach a false expectation. Whichever plan implements it must cover both and prove it on both.
  DO NOT REMOVE A GATE WHEN A WORK KIND CHANGES AWAY FROM `bug`. A gate may have been set deliberately for another reason, and silently clearing it would lose a decision; leave it and let a human clear it explicitly.
  - Depends on: E-01
  - Expected outcome: a recorded statement, in this plan and in its history, that this half is deferred to `b5sfwm`, citing that plan's status and the absence of the flag from `aw backlog set --help`, plus the two-dispatch-path requirement handed to it. If `b5sfwm` HAS executed by then, instead: reclassifying an item to `bug` applies the gate and reports it on BOTH spellings, and reclassifying away from `bug` leaves any existing gate untouched.
  - Execution state: performed
  - Execution note: THIS IS THE IMPLEMENTATION BRANCH, NOT THE DEFERRAL. `b5sfwm` HAS EXECUTED since review (decision D1): it now sits in `.aw/records/plans/executed/` with its status field reading `executed`, and `aw backlog set --help` lists `--work-kind {bug,chore,feature,followup,security}`. The deferral's sole stated cause ("there is NO flag on this verb for a reclassification to arrive through") is therefore measurably false, and this E-item's own text pre-authorizes this branch, so recording a deferral would have written a false statement into the permanent record while leaving the leak open. BOTH DISPATCH PATHS ARE COVERED, which this E-item named as the trap: the `--status` spelling in `backlog.run_set` and the positional spelling in `status_set.apply_status_change`, each delegating to the SAME `decide_gate_default` predicate and writing through the SAME `releases.set_blocks_release_line` primitive. The positional path is deliberately scoped to `rec.record_type == "backlog"` (decision D4), because that function is shared with plans and specs where `- Work-Kind:` is a recognized-but-optional DESCRIPTIVE field; defaulting a release gate there would invent a release obligation from a descriptive edit, and a plan's gate legitimately arrives by graduation (E-03) instead. NO GATE IS EVER REMOVED when a work kind changes away from `bug`: the predicate is consulted only for the kind the item is BECOMING, and it declines when a gate already exists, so a gate set deliberately for another reason survives.

### Task group 2: stop losing it at graduation

- [x] E-03 MAKE THE GRADUATION INHERITANCE REAL RATHER THAN PROSE, ON THE ONE ROUTE A SETTER OWNS. `AGENTS.md:38` already tells an agent to inherit the item's gate, and the measurement shows that instruction is not followed: 11 of 11 graduated gateless bugs have a `- From-Backlog:` carrier and 0 of the 13 carriers carries a gate. Make the tooling carry it on the route it can: when `aw ipd set --from-backlog <id6>` is applied and that item carries `- Blocks-Release:`, write the same value onto the plan and report it. Funnel through the existing shared `releases.set_blocks_release_line` primitive beside the existing `set_from_backlog_line` write (`status_set.py:706-733`), not a second writer.
  THE ROUTE INVENTORY IS ALREADY MEASURED AND IT SHRINKS THIS ITEM'S CLAIM SHARPLY (PR-004). Do NOT restate the plan's original framing that this closes the leak. Traced at review by git provenance, 12 of the 13 existing carriers carry `- From-Backlog:` in the file's FIRST commit, so they were hand-authored at scaffold time and no setter was ever involved; only 1 gained the field later. And `aw ipd scaffold` accepts NO `--from-backlog` flag (driven at review: its options are `--kind --title --path --set --order --legacy-name --author --apply --overwrite`), so the authoring route cannot be covered by adding a default to it either. `--from-backlog` exists on exactly ONE parser, `p_ipd_set` (`cli.py:1292-1297`); `aw specs set` does NOT have it, so a spec-first graduation has no setter route at all even though `AGENTS.md` and `check_engine.find_from_backlog_artifacts` both accept a spec as a legitimate carrier.
  STATE THE RESIDUAL AS THE DELIVERABLE, NOT AS A CAVEAT. This item strictly reduces FUTURE mismatch on one route and leaves the dominant historical route (hand authoring) to child 03's checker. Write that division of labour down where child 03 will read it, and name the spec-setter gap explicitly as unclosed rather than implying parity with plans. An inheritance that works on one route and not the other is worse than none if it is reported as complete: it teaches false confidence.
  DO NOT MAKE IT A REFUSAL. Writing the gate is safe; refusing `--from-backlog` when the gate cannot be applied would break a link the author is legitimately recording, and `check.from-backlog-gate-mismatch` already ships at ERROR to catch the mismatch afterwards.
  - Depends on: E-02
  - Expected outcome: `aw ipd set --from-backlog <gated item>` applies that item's gate to the plan and reports it, through the shared line writer; the inventory of every `From-Backlog` acquisition route is recorded with each marked covered or not, including `aw ipd scaffold` (no flag) and `aw specs set` (no flag), and the uncovered routes are named for child 03.
  - Execution state: performed
  - Execution note: wired into `status_set.apply_status_change` directly BESIDE the existing `set_from_backlog_line` write, funnelling through the shared `releases.set_blocks_release_line` primitive (no second writer), with the item lookup in one new `backlog.blocks_release_of_item` helper placed beside `existing_backlog_ids`/`_iter_items` so the backlog module stays the only reader of a backlog item's metadata. It is a WRITE, NEVER A REFUSAL, per this item's instruction. Three precedence rules, each tested: an explicit `--blocks-release` in the same call wins; an existing gate on the carrier is NEVER overwritten (a plan may legitimately gate a release its originating item never knew about, which is the shipped asymmetry the mismatch rule deliberately permits); and `--from-backlog -` writes no gate.
    THE RESIDUAL IS THE DELIVERABLE, AND RE-MEASURING IT REVERSED REVIEW'S CONCLUSION (decision D5). Re-derived at HEAD `af5fa26e`: 180 `From-Backlog` carriers across plans and specs, of which 77 carry the field in the file's FIRST commit (hand-authored, uncovered) and 103 gained it LATER (the setter route this item covers). Review measured 13 carriers with 12 hand-authored and concluded the setter route was the MINORITY (1 of 13); it is now the MAJORITY (103 of 180), so E-03 reaches further than the plan credits it with. The claim is NOT widened beyond that measurement: 77 hand-authored carriers remain uncovered, `aw ipd scaffold` still has NO `--from-backlog` flag (options driven this turn: `--kind --title --path --set --order --legacy-name --author --apply --overwrite`), and `aw specs set` still has none either, so a spec-first graduation still has no setter route. Those two gaps plus the hand-authoring population are handed to child 03 unchanged.

- [x] E-04 TEST THE DEFAULTS, THE ESCAPES AND THE NON-REGRESSIONS in a new `tests/test_bug_gate_default.py`, with a falsification pass: every assertion must be shown to FAIL against the pre-change code, since one that passes both before and after proves nothing. A test whose subject was DEFERRED (E-02) is not written as a skip pretending to cover it; state the absence instead.
  THE CASE LIST IS NOW FIXED BY MEASUREMENT AND MUST INCLUDE THE TWO REGRESSION GUARDS REVIEW HIT (PR-005). Cover: (1) a bug with no flag is gated `next`; (2) the default is REPORTED on the human surface; (3) the default is REPORTED on the `--agent` surface; (4) an explicit `-` yields an ungated bug; (5) `--work-kind chore` is NOT gated; (6) an explicit `--blocks-release <id6>` is not overwritten by the default; (7) NO RELEASE RECORD EXISTS and the flag is ABSENT: the item is created UNGATED with exit 0 and a notice, which is the case whose refusal broke 10 existing tests at review; (8) NO RELEASE RECORD EXISTS and `--blocks-release next` is EXPLICIT: still exit 2, which is the shipped contract `tests/test_backlog.py:254` pins; (9) `--status done --work-kind bug` is NOT gated, and the created item feeds `check_engine.check_release_gate_consistency` with ZERO findings, which is the assertion that pins PR-002 shut; (10) `aw ipd set --from-backlog <gated item>` writes the gate onto the plan.
  RUN THE FOUR ALREADY-AFFECTED FILES EXPLICITLY, not only the new one, and paste each. Review measured that a naive E-01 breaks `tests/test_backlog.py`, `tests/test_backlog_work_kind_rename.py`, `tests/test_backlog_blocking_close_gate.py` and `tests/test_release_gate_close.py`; those four are the blast radius, and a green new file alongside a red old one is the exact failure this instruction prevents. Do NOT "fix" them by adding a release record to their fixtures: their gateless-repo shape is the adopter-repo case E-01 must support, so if a fixture needs changing, say why and treat it as a finding about E-01 rather than about the fixture.
  - Depends on: E-03
  - Expected outcome: the ten cases above in the new file, each shown failing against pre-change code where it can (a case asserting UNCHANGED pre-existing behavior, such as case 8, is exempt from falsification and must be labelled as a REGRESSION GUARD rather than silently counted as new coverage); plus the four affected existing files run and pasted green.
  - Execution state: performed
  - Execution note: `tests/test_bug_gate_default.py`, 20 tests in three classes, with all ten mandated cases present as `case_01_*` .. `case_10_*` method names so the mapping is checkable rather than asserted. E-02's tests are written as REAL COVERAGE, not skips, because that half was implemented rather than deferred. The falsification pass ran the file against genuinely pre-change sources (`agent_workflows/backlog.py` and `status_set.py` restored to HEAD with only the new test file added) and produced `13 failed, 7 passed`: the 13 are the new behavior, and the 7 that pass BOTH before and after are REGRESSION GUARDS asserting unchanged shipped behavior, labelled as such and not counted as new coverage. They are case 04 (the `-` escape), case 06 (an explicit value is not overwritten), case 08 (the explicit-unresolvable refusal, which E-04 named), and four graduation-precedence guards. NO FIXTURE IN ANY EXISTING FILE WAS MODIFIED: the four blast-radius files went from `97 passed` at baseline to `97 passed` after, so the adopter-repo shape E-01 must support was never traded away to make a test pass.

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `run_new` already validates `--blocks-release` through `releases.resolve_release` and refuses an unresolvable value (`backlog.py:388-397`), so a default must reuse that validation rather than trusting `next`. But it must reuse it as a PREDICATE (default only if it resolves), NOT as a refusal, for the reason in E-01.
- The flag already distinguishes an ABSENT value from an explicit `-` (`br is not None and br != "-"`), which is exactly the distinction a default needs in order to leave an escape.
- `next` resolves to the single `planned` release record; measured, that is `f33nrj` (2.0.0).
- A FRESHLY INSTALLED REPO HAS NO RELEASES DIRECTORY. Driven at review: `aw install` into an empty repo creates no `.aw/records/releases/`, and `resolve_release` returns None when the directory is absent (`releases.py:138-141`). So "no planned release" is the NORMAL state of an adopter repo, not an edge case, and any behavior keyed on `next` resolving must degrade rather than refuse.
- A GATED `done` ITEM IS A SHIPPED ERROR. `check.blocking-item-closed-without-gate` is registered at `error` under `I-07` (`check_engine.py:105-107`) and its commit-scoped rule fires on a staged `done` item carrying `Blocks-Release` with no handoff/evidence/de-gate (`check_engine.py:2170-2199`). The `done` skip in E-01 exists for this rule.
- THE HUMAN AND AGENT OUTPUT SURFACES ARE SEPARATE RETURNS in `run_new` (`backlog.py:414-462`): the `--agent`/`--json` branch emits a `CommandResult` and returns before the human `sys.stdout.write`, so a notice must be carried in both.
- `aw backlog set` FORKS ON WHETHER `--status` WAS PASSED (`cli.py:11270-11286`), giving two write paths (`status_set.apply_status_change` and `backlog.run_set`). Any setter-side default must cover both.
- `--from-backlog` is registered on EXACTLY ONE parser, `p_ipd_set` (`cli.py:1292-1297`). `aw specs set` does not have it and `aw ipd scaffold` has no gate/link flags at all, so the setter route is narrow.
- `AGENTS.md:38` already states the graduation inheritance obligation in prose, and it is measurably not honored, which is why E-03 moves it into tooling; but 12 of 13 existing carriers were hand-authored, so the setter route covers the future, not the past.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | Creation applies no gate. `run_new` reads the flag and does nothing when it is absent, so a bug item is born ungated; re-measured at review, 22 of 68 live bugs are in that state (10 `open`, 11 `graduated`, 1 `blocked`). |
| F-2 | HIGH | Graduation loses the gate too, and prose does not prevent it: `AGENTS.md:38` instructs inheritance, yet 11 of 11 graduated gateless bugs have a carrier and 0 of the 13 carriers carries a gate. |
| F-3 | BLOCKER | REFUSING WHEN `next` DOES NOT RESOLVE BREAKS THE TOOL IN A FRESH REPO. Measured at review by implementing E-01 as written: 10 existing tests failed, and `aw install` on an empty repo creates no releases directory at all, so `aw backlog new --work-kind bug` would refuse in every newly installed adopter repo. The default must fall back to ungated on an ABSENT flag while still refusing an EXPLICIT unresolvable value. Fixed in E-01 (PR-001). |
| F-4 | HIGH | THE DEFAULT MANUFACTURES AN IMMEDIATELY-ILLEGITIMATE ITEM ON `--status done`. Driven through the CLI at review with the patched code, then staged: the shipped `check_engine.check_release_gate_consistency` returned one `check.blocking-item-closed-without-gate` (ERROR). The setter refuses this transition (exit 1, verified); creation would not. Fixed by the `done` skip in E-01 (PR-002). |
| F-5 | MEDIUM | THE GRADUATION HALF IS NARROWER THAN CLAIMED. Traced by git provenance: 12 of 13 carriers carry `From-Backlog` in their first commit (hand-authored), only 1 gained it later, `aw ipd scaffold` has no such flag, and `aw specs set` has no `--from-backlog` at all. E-03 reduces future mismatch on one route and does not close the historical leak (PR-004). |
| F-6 | MEDIUM | A NOTICE ON THE HUMAN SURFACE ALONE IS INVISIBLE TO A RUNNER. `run_new`'s `--agent`/`--json` branch returns before the human write (`backlog.py:414-462`), so OQ-01's "announce it" is only honored if the fact is carried in the structured result too (PR-003). |
| F-7 | MEDIUM | A default has an unambiguous target: `next` resolves to exactly one `planned` release (`f33nrj`, 2.0.0, re-verified). But it must be checked rather than assumed, or the tool writes a gate `check.blocks-release-dangling` immediately flags. |
| F-8 | MEDIUM | An escape is required, not optional. The author may legitimately file an ungated bug, and the existing absent-versus-`-` distinction already supports that, so a default must not become a prohibition. |
| F-9 | MEDIUM | E-02's dependency is not merely unlanded, it is UNREACHABLE as written: `b5sfwm` is `reviewed`/`go-pending-approval` in `pending/`, and `aw backlog set --help` lists no `--work-kind`, so no reclassification can arrive. The deferral is the expected deliverable, and whoever lands it must cover BOTH dispatch paths (PR-006). |
| F-10 | LOW | The authored provenance anchor is unresolvable: `git cat-file -t 2ff2b1b1` reports "Not a valid object name" in this repository, so every figure attributed to that HEAD had to be re-derived (PR-009). |

## Proposed changes (ordered, validatable)

1. Default the gate at creation for `bug`: resolve-or-fall-back (never refuse on an absent flag), skip `done`, report on both output surfaces, keep the explicit-`-` escape and the explicit-value refusal (E-01).
2. Record the deferral of the reclassification default to `b5sfwm`, with the two-dispatch-path requirement handed to it (E-02).
3. Apply the gate on `aw ipd set --from-backlog`, through the shared line writer, and record the full route inventory including the two uncovered surfaces (E-03).
4. Test the ten cases including the two regression guards, with falsification, and run the four affected existing files (E-04).

## Deferred / out of scope (with reason)

- ENFORCEMENT AND BACKFILL. Child 03 owns the checker and the existing violations (22 at review, not 28), deliberately after this child so the backfill cannot immediately re-diverge.
  - Carrier: rgaasb
- OTHER WORK KINDS. The parent's OQ-01 asks about `security`; not assumed here.
  - Carrier: 0htqmm
- DETECTING A DEFECT FILED AS `chore`. The gate keys on the author's classification and cannot see a mislabelled defect; the parent's OQ-02 measures that leak and child 01 states it as a limit.
  - Carrier-Declined: the parent's OQ-02 was resolved by the maintainer's perceptibility test and explicitly proposes NO MECHANISM, because a reviewer-side audit of every `chore` would be a second classification pass with the same judgement problem one layer down. The honest control is a stated test plus review, and child 01 `zqs0px` (now `executed`) already wrote that limit into the contributor rules. So nothing is outstanding to build, and a carrier would assert a work item that this Set deliberately decided not to create.
- THE HAND-AUTHORING ROUTE TO `From-Backlog`. Re-measured at execution: 77 of 180 current carriers (review measured 12 of 13, and the setter route has since become the MAJORITY at 103 of 180). No setter is involved, `aw ipd scaffold` has no such flag, and adding gate inference to the authoring path would mean a scaffolder that reads the backlog tree. Named here as a deliberate exclusion and handed to child 03's checker, because E-03's value is bounded by it and pretending otherwise would misreport this child as closing the leak.
  - Carrier: rgaasb
- A `--from-backlog` FLAG ON `aw specs set`. A spec is an accepted gate carrier (`check_engine.find_from_backlog_artifacts` scans specs; `AGENTS.md` names both), yet the flag exists only on `p_ipd_set`, so a spec-first graduation has no setter route. Adding it is a new CLI surface on another verb, outside this child's declared paths and its concern; recorded so the asymmetry is a known gap rather than an oversight. Re-confirmed missing at execution by driving `aw specs set --help`.
  - Carrier: mod4ml
- THE RECLASSIFICATION DEFAULT ITSELF, which this plan DEFERRED to `b5sfwm` at authoring time.
  - Carrier-Declined: SUPERSEDED AT EXECUTION, so there is no longer an obligation to carry. `b5sfwm` has EXECUTED and `aw backlog set` now carries `--work-kind`, so E-02 took its own pre-authorized implementation branch and shipped the default on BOTH dispatch paths rather than deferring. See E-02's execution note and decision D1.

## Scope check

- Over-scope: none. Three paths: the backlog module where the flag is read, the CLI where the setters are wired, and one new test file.
- Under-scope, and now MEASURED rather than asserted: a plan that declares `From-Backlog` at authoring time with no setter involved is not covered by E-03, and that is 12 of the 13 existing carriers, so this child closes the MINORITY route. `aw specs set` has no `--from-backlog` at all, so a spec-first graduation is uncovered entirely. Both are named for child 03's checker and this child does not claim to close either.
  RE-MEASURED AT EXECUTION AND THE MINORITY/MAJORITY CLAIM IS NOW INVERTED: 180 carriers, 77 hand-authored (first commit) and 103 acquired later, so E-03 covers the MAJORITY route, not the minority. The under-scope itself is unchanged and real (77 uncovered carriers, plus the `aw specs set` gap), so this child still does not claim to close either; only the proportion moved. See decision D5 and V-03.
- A SCOPE-PATHS QUESTION THE EXECUTOR MUST SETTLE, not silently: `agent_workflows/command_surface.py` declares `backlog new`'s accepted flag set (`command_surface.py:1170-1195`) and a declaration-agreement test exists for that surface. E-01 adds no new FLAG, so the declaration should not need to change; but if the implementation does touch it, that path is NOT in `- Scope-Paths:` and must be justified at finalize with a `--scope-reason`, or declared before execution. Do not edit it without doing one of the two.
  SETTLED AT EXECUTION: `command_surface.py` was NOT touched, as predicted. E-01 adds no flag (the default is applied when a flag is ABSENT), so the declared flag set is unchanged and `git status` shows that path outside the changed set. The declaration test was nevertheless run to check rather than assume; it FAILS, on five undeclared `oc profile` leaves entirely unrelated to this plan, and the failure reproduces with this plan's source edits stashed. Filed as backlog `4fe3al` rather than fixed here, because fixing it would be the unjustified out-of-scope edit this paragraph warns against.

- THE ACTUAL SCOPE DELTA, stated plainly for the finalize reconciliation rather than left to be discovered. Declared: `agent_workflows/backlog.py`, `agent_workflows/cli.py`, `tests/test_bug_gate_default.py`. Changed: `agent_workflows/backlog.py`, `agent_workflows/status_set.py`, `tests/test_bug_gate_default.py`.
  - ONE UNDECLARED PATH WAS CHANGED: `agent_workflows/status_set.py`, and it needs a `--scope-reason`. THE PLAN'S OWN CITATIONS POINT AT THIS FILE while `- Scope-Paths:` names `cli.py` instead, so the declaration is simply mis-typed rather than the change being out of scope: E-03 instructs "funnel through the existing shared `releases.set_blocks_release_line` primitive beside the existing `set_from_backlog_line` write (`status_set.py:706-733`)", and E-02's trap note cites `status_set.py:706-773`. Both name the file the work had to land in, and `cli.py` holds only the argparse registration, which needed no edit because `--from-backlog` and `--work-kind` already exist there. Suggested reason: `agent_workflows/status_set.py=the write site E-02/E-03 explicitly cite; Scope-Paths named cli.py, which holds only the flag registration and required no change`.
  - ONE DECLARED PATH WAS NOT MODIFIED: `agent_workflows/cli.py`, needing a `--scope-ack` (e.g. `--scope-ack agent_workflows/cli.py=no-flag-added; both setters already registered`).

## Required tests / validation

`tests/test_bug_gate_default.py` with a falsification pass against pre-change code. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste it, and judge on the failure-SET delta rather than on a number. FOR REFERENCE ONLY, review measured it bare with the corrected E-01 patch applied in a throwaway copy: `5971 passed, 3 skipped, 2 xfailed in 58.71s`. Do NOT quote that as your baseline; re-measure. Run the suite BARE: the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0` or a second `-q` makes the run slower and suppresses the summary line the contract requires you to paste.

RUN THE FOUR ALREADY-MEASURED BLAST-RADIUS FILES AS THEIR OWN CHECKPOINT, not only as part of the bare run: `tests/test_backlog.py`, `tests/test_backlog_work_kind_rename.py`, `tests/test_backlog_blocking_close_gate.py`, `tests/test_release_gate_close.py`. Review measured `10 failed, 77 passed` across those four with a naive E-01 and `87 passed` with the corrected one, so they are the fastest signal that E-01 was implemented the right way, and a red result there is a design finding rather than a fixture problem.

ALSO ESTABLISH A CHECKER BASELINE, because this child's specific hazard is a shipped ERROR rule rather than pytest. Before the first edit record the finding count of `check_engine.check_release_gate_consistency` on the live tree (review measured ZERO), and after the change confirm it is unchanged. That is the assertion PR-002 exists to protect.

## Spec / documentation sync

N/A with reason: child 01 states the rule in the contributor rules and the decisions log, and this child implements it. If E-01's notice or the reported default needs documenting beyond that, add it to child 01's text rather than duplicating policy here.

ONE THING THIS CHILD MUST HAND BACK TO CHILD 01, since it changes what child 01's text can truthfully claim: the default is BEST-EFFORT, not guaranteed. It applies only when a `planned` release record exists, and a freshly installed repo has none (measured). So child 01 must not write that a bug "always" carries a gate; the honest statement is that the tool applies it when it can and reports when it cannot. Tell child 01 rather than adding the caveat here, because the two documents would then disagree.

HANDBACK DISCHARGED AT EXECUTION, AND NO EDIT TO CHILD 01'S TEXT IS NEEDED. Child 01 `zqs0px` has executed, so its text was READ rather than guessed at. `AGENTS.md`'s "Every live bug gates the next release" section (line 146, i.e. below the `<!-- /aw:block -->` marker at line 108, so repo-local and editable had a fix been required) states an OBLIGATION ON THE AUTHOR: "a backlog item, spec, or plan whose `- Work-Kind:` is `bug` ... MUST carry `- Blocks-Release:` while it is LIVE". It nowhere claims the TOOL always applies the gate, and nowhere says a bug automatically carries one. So the feared overclaim is ABSENT and the honest statement this child was told to enforce is already what the document says: the rule binds the author, and this child's tooling helps where it can. That text also already names `0htqmm` as the carrier for making the gating set configurable, which matches `GATE_DEFAULT_KINDS` exactly. No edit was made, which is why `AGENTS.md` is correctly absent from this plan's changed paths.

NO CLI HELP TEXT CHANGES ARE REQUIRED BY THIS CHILD, verified: `--blocks-release`'s help on `backlog new` already reads "a release id6, 'next', or '-' to omit", which stays true. If the executor decides the defaulting behavior belongs in that help string, that is an in-scope edit to `cli.py` (already declared) and should be stated as such, but it is not mandated: the runtime notice E-01 requires is the load-bearing signal.

## Open questions

### OQ-01: Should the creation default be silent or announced?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: ANNOUNCE IT ON BOTH SURFACES, and E-01 is now written that way. A field the tool wrote but the author did not type is exactly the kind of hidden behavior that makes a later reader distrust the record, and the repository's own precedent is directly on point and now cited precisely: the maintainer's 2026-09-10 ruling on plan `y4adch` OQ-01 was "FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE", with silent fallback explicitly declined because "a repository that believes it set a policy would be overridden with no signal anywhere". That ruling also fixes WHAT the notice must contain to be actionable rather than noise: the field, the value applied, and why.
  REVIEW ADDED THE HALF THAT MAKES IT REAL (PR-003): announcing on the human surface alone does not satisfy this, because `run_new`'s `--agent`/`--json` branch returns before the human write (`backlog.py:414-462`) and a runner is the most likely caller. The fact must be carried in the structured result too. That is now an E-01 requirement and a tested case (E-04 case 3), so the question is resolved rather than left to the executor's tidiness.

### OQ-02: Does the same 2026-09-10 fall-back-and-warn precedent govern the absent-release case?

- Blocking: no
- Status: resolved
- Owner: this plan's reviewer, resolved from repository evidence
- Resolution or deferral rationale: YES, AND IT IS THE REASON PR-001 CHOSE FALLBACK OVER REFUSAL. The plan originally instructed a REFUSAL when `next` does not resolve, which is the fail-closed posture. The maintainer settled that exact trade-off on 2026-09-10 for a shared tracked file: fail-closed was "declined on blast radius", because one bad state would refuse every invocation for every human and agent in the checkout, whereas a per-invocation mistake harms only the caller who typed it. The shapes match precisely: an ABSENT flag in a repo with no release record is the repository-state case (fall back and warn), while an EXPLICIT unresolvable `--blocks-release` is the per-invocation case (refuse, which already ships and E-01 preserves). So the asymmetry E-01 now prescribes is not an invention; it is the same asymmetry the maintainer already chose, applied to a new surface.
  MEASURED CONSEQUENCE OF GETTING IT WRONG: the refusal broke 10 existing tests and would break `aw backlog new --work-kind bug` in every freshly installed adopter repo. Recorded as a resolved decision rather than asked, because the repository answered it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste FIVE driven cases from a scratch repo, each with its unpiped exit code. (1) `aw backlog new --work-kind bug` with NO gate flag and a `planned` release present: show the created item's `- Blocks-Release: next` line AND the human notice. (2) The same command with `--agent`: paste the JSONL record and point at the field carrying the defaulted-gate fact, since a human-only notice does not satisfy E-01. (3) `--blocks-release -`: show an UNGATED item, exit 0. (4) NO release record and NO flag: show an UNGATED item, exit 0, and the notice explaining why; a refusal here is a FAILED validation, because it is the regression PR-001 exists to prevent. (5) NO release record and an EXPLICIT `--blocks-release next`: show exit 2 and that no file was written, proving the shipped refusal did not regress.
    ALSO paste the `--status done --work-kind bug` case: the created item must carry NO gate, and feeding it to `check_engine.check_release_gate_consistency` (staged) must return ZERO findings. Review measured ONE `check.blocking-item-closed-without-gate` without this skip, so a missing or unpasted result here is a failed validation, not a formality.
  - Observed evidence: all six cases driven through the CLI in two scratch repos (`withrel` carries one `planned` release `f33nrj`; `norel` has NO `.aw/records/releases/` at all, the fresh-`aw install` shape).

    CASE 1, bug with NO gate flag, planned release present:

    ```text
    $ python3 -m agent_workflows backlog new --dir <withrel> --work-kind bug --summary "case one" --slug c1 --apply
    aw backlog new: defaulted - Blocks-Release: next on this bug (no --blocks-release given): every live bug gates the next release; pass '--blocks-release -' to file an ungated bug
    aw backlog new: wrote <withrel>/.aw/records/backlog/open/20260918-5ynqrj-01-5ynqrj-c1.backlog.md
    exit=0
    $ cat <created item>
    - Id: 5ynqrj
    - Status: open
    - Blocks-Release: next
    - Set: 5ynqrj
    - Priority: medium
    - Work-Kind: bug
    - Summary: case one
    ```

    CASE 2, the same command with `--agent`. THE FIELD CARRYING THE FACT is `evidence`, which is what survives into the COMPACT record (`data` is omitted there); note `findings:0`, which is why an `info` `Diagnostic` was rejected:

    ```text
    $ python3 -m agent_workflows backlog new --dir <withrel> --work-kind bug --summary "case two" --slug c2 --apply --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"backlog new","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"changes":[{"kind":"create","path":".aw/records/backlog/open/20260918-kf6pn1-01-kf6pn1-c2.backlog.md"}],"evidence":["blocks-release-default:next"],"next":null}
    exit=0
    ```

    The FULL `--json` surface additionally carries the machine-readable triple:

    ```text
    "data": {"path": "...", "id": "vm7rne", "blocks_release": "next", "blocks_release_defaulted": true,
             "blocks_release_default_notice": "defaulted - Blocks-Release: next on this bug (no --blocks-release given): ..."}
    ```

    CASE 3, the explicit `-` escape, exit 0 and UNGATED:

    ```text
    $ python3 -m agent_workflows backlog new --dir <withrel> --work-kind bug --blocks-release - --summary "case three" --slug c3 --apply
    aw backlog new: wrote <withrel>/.aw/records/backlog/open/20260918-7rhfk6-01-7rhfk6-c3.backlog.md
    exit=0
    $ grep -c Blocks-Release <item c3>
    0
    ```

    CASE 4, NO release record and the flag ABSENT. NO REFUSAL, exit 0, ungated, with the reason. This is the regression PR-001 exists to prevent:

    ```text
    $ python3 -m agent_workflows backlog new --dir <norel> --work-kind bug --summary "case four" --slug c4 --apply
    aw backlog new: not defaulting - Blocks-Release: on this bug because 'next' does not resolve to a single planned release record; file it ungated and set the gate with `aw backlog set --blocks-release next` once a planned release exists
    aw backlog new: wrote <norel>/.aw/records/backlog/open/20260918-ugyt7m-01-ugyt7m-c4.backlog.md
    exit=0
    $ cat <item c4>          # no Blocks-Release line
    - Id: ugyt7m
    - Status: open
    - Set: ugyt7m
    - Priority: medium
    - Work-Kind: bug
    - Summary: case four
    ```

    CASE 5, NO release record and an EXPLICIT `--blocks-release next`: the shipped refusal did NOT regress, and nothing was written:

    ```text
    $ find <norel>/.aw/records/backlog -name '*.backlog.md'   # before
      20260918-ugyt7m-01-ugyt7m-c4.backlog.md
    $ python3 -m agent_workflows backlog new --dir <norel> --work-kind bug --blocks-release next --summary "case five" --slug c5 --apply
    aw backlog new: --blocks-release 'next' does not resolve to a release record
    exit=2
    $ find <norel>/.aw/records/backlog -name '*.backlog.md'   # after: no c5, nothing written
      20260918-ugyt7m-01-ugyt7m-c4.backlog.md
    ```

    THE `--status done --work-kind bug` CASE, created UNGATED, then staged and fed to the SHIPPED checker:

    ```text
    $ python3 -m agent_workflows backlog new --dir <withrel> --work-kind bug --status done --summary "case done" --slug cdone --apply
    aw backlog new: not defaulting - Blocks-Release: on this bug because its status is 'done': a gated done item is rejected by check.blocking-item-closed-without-gate, and a parked maybe is not live work
    aw backlog new: wrote <withrel>/.aw/records/backlog/done/20260918-dmw4s8-01-dmw4s8-cdone.backlog.md
    exit=0
    $ cat <item cdone>       # no Blocks-Release line; leading '- ' stripped below so this
                             # BACKLOG item's status line is not misread as this PLAN's
      Id: dmw4s8
      Status: done
    ...
    $ git -C <withrel> diff --cached --name-only | grep cdone
    .aw/records/backlog/done/20260918-dmw4s8-01-dmw4s8-cdone.backlog.md
    $ python3 -c 'CE.check_release_gate_consistency(<withrel>)'
    findings: 0
    ```

    THE COUNTERFACTUAL, so this is not merely an observation of a clean tree: writing the gate the default WOULD have applied onto that same staged `done` item produces exactly the ERROR the skip avoids.

    ```text
    $ # set_blocks_release_line(<item cdone>, 'next'); re-stage; re-run the checker
    findings: 1
      check.blocking-item-closed-without-gate | a done backlog item staged in this commit still carries Blocks-Release with no handoff (From-Backlog plan), resolvable evidence, or de-gate; close it via `aw backlog set done` (which enforces the gate) rather than by hand
    ```

    The `parked` skip behaves identically (`not defaulting ... because its status is 'parked'`, exit 0, ungated). Automated equivalents of every case above are in `tests/test_bug_gate_default.py` (cases 01-09 plus `test_parked_bug_is_not_gated`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the EXPECTED outcome is a deferral, so paste the deferral evidence: `b5sfwm`'s `- Status:` and `- Readiness:` lines, its directory, and `aw backlog set --help` showing no `--work-kind` flag. Then paste the recorded deferral statement as written into this plan, including the two-dispatch-path requirement handed to whoever lands it, and say EXPLICITLY that this half is not delivered. If `b5sfwm` HAS executed by then, instead paste a reclassification to `bug` showing the gate applied and reported on BOTH spellings (positional and `--status`), and a reclassification AWAY from `bug` showing an existing gate untouched. Do NOT mark this complete on a claim that the flag was unavailable without pasting the `--help` output that proves it.
  - Observed evidence: THE SECOND BRANCH APPLIES: `b5sfwm` HAS EXECUTED, so this validates the IMPLEMENTATION, not a deferral. The disproof of the deferral's premise is pasted first, because V-02 forbids claiming the flag's state without showing it:

    ```text
    $ find .aw/records/plans -name '*b5sfwm*'
    .aw/records/plans/executed/20260908-bklgkind-01-b5sfwm-give-aw-backlog-set-the-work-kind-and-priority-setters-its-p.ipd.md
    $ grep -m1 '^- Status:' <that file> | tr -d '-' | tr -s ' '
     Status: executed
    $ python3 -m agent_workflows backlog set --help
      --work-kind {bug,chore,feature,followup,security}
                            Set the item's Work-Kind
                            (bug|chore|feature|followup|security). Persists on a
                            no-op transition. No '-' clear: the field is REQUIRED
                            on a backlog item (OQ-02).
      --priority {high,low,medium}
                            Set the item's Priority (high|low|medium). ...
    ```

    So the flag EXISTS (review measured its absence) and the deferral is no longer available; see decision D1.

    SPELLING 1, POSITIONAL (`aw backlog set <status> <selector>`, routing through `status_set.apply_status_change`), chore -> bug:

    ```text
    $ python3 -m agent_workflows backlog set open 7zb3bg --dir <scratch> --work-kind bug --yes --no-commit
    aw backlog set: defaulted - Blocks-Release: next on this bug (no --blocks-release given): every live bug gates the next release; pass '--blocks-release -' to file an ungated bug
    -    backlog     20260918-7zb3bg-01-7zb3bg  [medium]  unchanged
    exit=0
    $ cat <item A>
    - Id: 7zb3bg
    - Status: open
    - Blocks-Release: next
    - Work-Kind: bug
    - Set: 7zb3bg
    - Priority: medium
    - Summary: reclassify me A
    ```

    SPELLING 2, `--status` (routing through `backlog.run_set`), chore -> bug:

    ```text
    $ python3 -m agent_workflows backlog set bqb2z1 --status open --dir <scratch> --work-kind bug --yes --no-commit
    aw backlog set: defaulted - Blocks-Release: next on this bug (no --blocks-release given): every live bug gates the next release; pass '--blocks-release -' to file an ungated bug
    aw backlog set: 20260918-bqb2z1-01-bqb2z1-reclass-b.backlog.md -> open
    exit=0
    $ cat <item B>
    - Id: bqb2z1
    - Status: open
    - Blocks-Release: next
    - Work-Kind: bug
    ...
    ```

    RECLASSIFYING AWAY FROM `bug` LEAVES THE EXISTING GATE, on BOTH spellings:

    ```text
    $ python3 -m agent_workflows backlog set open 7zb3bg --dir <scratch> --work-kind chore --yes --no-commit   # positional
    exit=0
    $ grep -E '^- (Work-Kind|Blocks-Release):' <item A>
    - Work-Kind: chore
    - Blocks-Release: next
    $ python3 -m agent_workflows backlog set bqb2z1 --status open --dir <scratch> --work-kind chore --yes --no-commit   # --status
    aw backlog set: 20260918-bqb2z1-01-bqb2z1-reclass-b.backlog.md -> open
    exit=0
    $ grep -E '^- (Work-Kind|Blocks-Release):' <item B>
    - Work-Kind: chore
    - Blocks-Release: next
    ```

    The three automated equivalents are `ReclassificationDefaultTests::test_positional_spelling_defaults_the_gate_on_reclassification`, `::test_status_spelling_defaults_the_gate_on_reclassification`, and `::test_reclassifying_away_from_bug_leaves_an_existing_gate`, and all three FAIL against pre-change code (see V-04's falsification list), which is what proves they cover new behavior rather than restating the status quo.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `aw ipd set --from-backlog <gated item>` and show the plan gaining the SAME gate value, plus the diff proving it went through `releases.set_blocks_release_line` (one metadata line, correct position) rather than a new writer. Then paste the ROUTE INVENTORY as a table: every path by which an artifact can acquire `From-Backlog`, each marked covered or not, and each backed by the command output or grep that establishes it. It MUST include `aw ipd set` (covered), `aw ipd scaffold` (no flag: paste its `--help`), `aw specs set` (no flag: paste its `--help`), and hand authoring (uncovered). An inventory claiming full coverage is a FAILED validation, because review measured 12 of 13 existing carriers as hand-authored; paste that provenance count or re-derive it.
  - Observed evidence: the graduation driven end to end in a scratch repo. The source item is a bug created by E-01's default (so the two halves are exercised together, not in isolation):

    ```text
    $ python3 -m agent_workflows backlog new --dir <scratch> --work-kind bug --summary "gated bug for graduation" --slug grad-src --apply
    aw backlog new: defaulted - Blocks-Release: next on this bug (no --blocks-release given): ...
    source item id=3dgcl8 gate=- Blocks-Release: next

    $ python3 -m agent_workflows ipd set to-review aaa111 --dir <scratch> --from-backlog 3dgcl8 --yes --no-commit
    aw set: inherited - Blocks-Release: next from backlog item 3dgcl8 (graduation handoff: the gate travels with the work)
    -    plan        20260918-gradset-01-aaa111  unchanged
    exit=0
    ```

    The plan BEFORE had no gate and no link; AFTER it carries both, the gate value MATCHING the item's:

    ```text
    $ grep -n -E '^- (Status|Blocks-Release|From-Backlog):' <plan>
    5:- Status: to-review
    6:- Blocks-Release: next
    7:- From-Backlog: 3dgcl8
    $ grep -c '^- Blocks-Release:' <plan>
    1
    ```

    THE SHARED-WRITER PROOF is the position plus the count: exactly ONE `- Blocks-Release:` line, inserted directly after `- Status:`, which is `releases.set_blocks_release_line`'s documented anchor, and the only gate writer named anywhere in the diff:

    ```text
    $ git diff -- agent_workflows/status_set.py | grep -E '^\+.*set_blocks_release_line'
    +                    tmp_text = _releases.set_blocks_release_line(
    +    # `backlog.run_set` call, and written through the SAME shared `releases.set_blocks_release_line`
    +            tmp_text = _releases.set_blocks_release_line(
    ```

    `test_case_10_ipd_set_from_backlog_inherits_the_items_gate` asserts the same three facts mechanically (value, single line, index immediately after `- Status:`) and additionally that the tree yields no `check.from-backlog-gate-mismatch`.

    THE ROUTE INVENTORY. Coverage is PARTIAL and this is the deliverable, not a caveat:

    | Route to `- From-Backlog:` | Covered by E-03? | Evidence |
    |---|---|---|
    | `aw ipd set --from-backlog <id6>` | YES | driven above; `--from-backlog` is registered on exactly one parser, `p_ipd_set` (`cli.py:1307-1312`) |
    | `aw ipd scaffold` at authoring time | NO: THE FLAG DOES NOT EXIST | `--help` options are exactly `--no-color --agent --json --kind --title --path --set --order --legacy-name --author --apply --overwrite`; there is no `--from-backlog` and no gate flag at all |
    | `aw specs set` (a spec is an equally valid gate carrier) | NO: THE FLAG DOES NOT EXIST | `--help` lists `--status --message --gate-kind --gate-ref --gate-summary --blocks-release --priority --work-kind --evidence --by-human --allow-open-questions --date --dry-run --yes --commit/--no-commit`; `--blocks-release` is present but `--from-backlog` is NOT, so a spec-first graduation has no setter route |
    | HAND AUTHORING (writing the bullet into the file) | NO, and it is a large population | 77 of 180 current carriers, re-derived below |

    THE PROVENANCE COUNT, RE-DERIVED RATHER THAN QUOTED, AND IT REVERSES REVIEW'S CONCLUSION (decision D5). Walking `.aw/records/plans` + `.aw/records/specs` for `- From-Backlog:` and tracing each file's first commit with `git log --follow --diff-filter=A`, at HEAD `af5fa26e`:

    ```text
    total From-Backlog carriers: 180
    carried From-Backlog in the file's FIRST commit (hand-authored): 77
    gained From-Backlog LATER (a setter route): 103
    ```

    Review measured 13 carriers, 12 hand-authored, and concluded the setter route covered "at most 1 of 13". The population has grown an order of magnitude and INVERTED: the setter route is now 103 of 180, the MAJORITY. So E-03 reaches materially further than the plan credits it with. The claim is deliberately not widened past the number: 77 hand-authored carriers remain uncovered, and the two missing flags above are UNCLOSED. All three are handed to child 03's checker, which is where the historical population belongs.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_bug_gate_default.py -o addopts=""` with per-test names, and confirm all ten E-04 cases are present by name. Paste the FALSIFICATION showing each NEW case FAIL against pre-change code, and label case 8 (the explicit-unresolvable refusal) as a REGRESSION GUARD that correctly passes both before and after rather than counting it as falsified coverage.
    THEN paste the four blast-radius files run together (`tests/test_backlog.py tests/test_backlog_work_kind_rename.py tests/test_backlog_blocking_close_gate.py tests/test_release_gate_close.py -o addopts=""`) showing them GREEN, and state whether any fixture was modified; if one was, justify it as a finding about E-01 rather than about the fixture. Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline, plus the checker baseline comparison showing `check_release_gate_consistency` unchanged.
  - Observed evidence: the new file, per test, POST-change. All ten mandated cases are present by name as `case_01_*` .. `case_10_*`:

    ```text
    $ python3 -m pytest tests/test_bug_gate_default.py -o addopts="" -v
    tests/test_bug_gate_default.py::ReclassificationDefaultTests::test_reclassifying_away_from_bug_leaves_an_existing_gate PASSED [  5%]
    tests/test_bug_gate_default.py::ReclassificationDefaultTests::test_positional_spelling_defaults_the_gate_on_reclassification PASSED [ 10%]
    tests/test_bug_gate_default.py::ReclassificationDefaultTests::test_status_spelling_defaults_the_gate_on_reclassification PASSED [ 15%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_09_status_done_bug_is_not_gated_and_checker_is_clean PASSED [ 20%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_01_bug_with_no_flag_is_gated_next PASSED [ 25%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_03_default_is_reported_on_the_agent_surface PASSED [ 30%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_07_no_release_record_and_absent_flag_is_ungated_exit_zero PASSED [ 35%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_parked_bug_is_not_gated PASSED [ 40%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_08_no_release_record_and_explicit_next_still_exits_two PASSED [ 45%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_06_explicit_gate_value_is_not_overwritten PASSED [ 50%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_02_default_is_reported_on_the_human_surface PASSED [ 55%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_05_chore_is_not_gated PASSED [ 60%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_decide_gate_default_is_the_single_shared_predicate PASSED [ 65%]
    tests/test_bug_gate_default.py::CreationDefaultTests::test_case_04_explicit_dash_yields_an_ungated_bug PASSED [ 70%]
    tests/test_bug_gate_default.py::GraduationInheritanceTests::test_existing_carrier_gate_is_never_overwritten PASSED [ 75%]
    tests/test_bug_gate_default.py::GraduationInheritanceTests::test_case_10_ipd_set_from_backlog_inherits_the_items_gate PASSED [ 80%]
    tests/test_bug_gate_default.py::GraduationInheritanceTests::test_ungated_item_leaves_the_plan_ungated PASSED [ 85%]
    tests/test_bug_gate_default.py::GraduationInheritanceTests::test_clearing_from_backlog_writes_no_gate PASSED [ 90%]
    tests/test_bug_gate_default.py::GraduationInheritanceTests::test_explicit_blocks_release_in_the_same_call_wins PASSED [ 95%]
    tests/test_bug_gate_default.py::GraduationInheritanceTests::test_blocks_release_of_item_lookup PASSED [100%]

    ============================== 20 passed in 0.45s ==============================
    ```

    THE FALSIFICATION PASS. `agent_workflows/backlog.py` and `agent_workflows/status_set.py` were restored to HEAD (`git checkout --`, verified: `git status --short` showed ONLY the untracked new test file) and the same file run against genuinely pre-change code:

    ```text
    ============================= FAILED (pre-change) =============================
    FAILED tests/test_bug_gate_default.py::ReclassificationDefaultTests::test_positional_spelling_defaults_the_gate_on_reclassification
    FAILED tests/test_bug_gate_default.py::ReclassificationDefaultTests::test_status_spelling_defaults_the_gate_on_reclassification
    FAILED tests/test_bug_gate_default.py::ReclassificationDefaultTests::test_reclassifying_away_from_bug_leaves_an_existing_gate
    FAILED tests/test_bug_gate_default.py::GraduationInheritanceTests::test_case_10_ipd_set_from_backlog_inherits_the_items_gate
    FAILED tests/test_bug_gate_default.py::GraduationInheritanceTests::test_blocks_release_of_item_lookup
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_case_09_status_done_bug_is_not_gated_and_checker_is_clean
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_case_03_default_is_reported_on_the_agent_surface
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_case_05_chore_is_not_gated
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_decide_gate_default_is_the_single_shared_predicate
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_case_02_default_is_reported_on_the_human_surface
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_case_01_bug_with_no_flag_is_gated_next
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_parked_bug_is_not_gated
    FAILED tests/test_bug_gate_default.py::CreationDefaultTests::test_case_07_no_release_record_and_absent_flag_is_ungated_exit_zero
    ========================= 13 failed, 7 passed in 0.61s =========================
    ```

    A representative pre-change failure, showing the notice simply absent:

    ```text
    >       self.assertIn("not defaulting", out)
    E       AssertionError: 'not defaulting' not found in 'aw backlog new: wrote /tmp/.../c7.backlog.md\n'
    ```

    THE SEVEN THAT PASS BOTH BEFORE AND AFTER ARE REGRESSION GUARDS, labelled as such in the file and NOT counted as new coverage. They assert pre-existing shipped behavior that must not regress: `test_case_08_no_release_record_and_explicit_next_still_exits_two` (the explicit-unresolvable refusal, which E-04 names explicitly), `test_case_04_explicit_dash_yields_an_ungated_bug`, `test_case_06_explicit_gate_value_is_not_overwritten`, and four graduation-precedence guards (`test_existing_carrier_gate_is_never_overwritten`, `test_explicit_blocks_release_in_the_same_call_wins`, `test_clearing_from_backlog_writes_no_gate`, `test_ungated_item_leaves_the_plan_ungated`). Cases 04 and 06 pass pre-change because the pre-change code applied NO default at all, so "an explicit value is honored" was already true; they are retained because the default must not break them, which is precisely a guard.

    THE FOUR BLAST-RADIUS FILES, GREEN, AND NO FIXTURE WAS MODIFIED:

    ```text
    $ python3 -m pytest tests/test_backlog.py tests/test_backlog_work_kind_rename.py tests/test_backlog_blocking_close_gate.py tests/test_release_gate_close.py -o addopts=""
    ============================== 97 passed in 2.78s ==============================
    ```

    Baseline for those four, captured BEFORE the first edit: `97 passed in 2.96s`. So the count is IDENTICAL and no fixture needed changing, which is the outcome E-01's fallback design predicts: their gateless-repo shape is the adopter-repo case, and it is now a supported path rather than a refusal. (Review measured `10 failed, 77 passed` with the naive refusing implementation; that failure mode did not recur.)

    THE BARE SUITE, AGAINST A BASELINE ESTABLISHED BEFORE THE FIRST EDIT:

    ```text
    BEFORE (pre-edit baseline): 8076 passed, 3 skipped, 2 xfailed in 160.70s (0:02:40)
    AFTER  (post-change):       8096 passed, 3 skipped, 2 xfailed in 155.98s (0:02:35)
    ```

    Failure-SET delta is EMPTY (zero failures before, zero after) and the +20 passed is exactly the 20 tests added by this plan, so no pre-existing test changed state.

    THE CHECKER BASELINE COMPARISON, which is this child's specific hazard rather than pytest:

    ```text
    BEFORE (pre-edit): check_release_gate_consistency -> 2 findings, both check.from-backlog-gate-mismatch
      20260912-doctorprobe-01-h90ij1-...ipd.md   (carrier 'f33nrj' vs item hdhzr2 'next')
      20260912-migleftover-01-z1yefm-...ipd.md   (carrier 'f33nrj' vs item x15f0q 'next')
    AFTER  (post-change): 2 findings, {'check.from-backlog-gate-mismatch': 2}, the SAME two files
    ```

    UNCHANGED, which is the assertion PR-002 exists to protect. Both findings are PRE-EXISTING and are NOT mine: each is a carrier spelling the gate as the id6 `f33nrj` where its item spells it `next`. They are reported as a defect finding rather than fixed here, because those plans are another party's artifacts and the spelling equivalence is outside this plan's declared paths.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: go-pending-approval`. It must not be executed until a human sets it `approved`.

It carries `- Item-Dependencies: executed:zqs0px` because the written rule is the authority this tooling implements; defaulting a gate before the policy is recorded would leave the behavior unexplained by any document.

It carries `- Blocks-Release: next` in line with the rule it implements.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push; an edit outside them is made and then JUSTIFIED at finalize with a `--scope-reason` per path (and a `--scope-ack` for a declared path you did not modify), not avoided by stopping. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. On completion, move this file to `.aw/records/plans/executed/` with the terminal `Status:` and a workflow-history line, as the `ipd-lifecycle` post-gate step.

RE-VERIFY THE INDEX BEFORE EVERY COMMIT AND AFTER ANY FAILED HOOK. This checkout is shared and was measurably being edited by another party during this review (a backlog item moved `open` -> `done` in the working tree, untouched by this review). `git diff --cached --name-only` must contain only paths you changed, and pre-commit's stash-and-restore can leave someone else's paths staged after a rejected commit; unstage precisely with `git restore --staged <path>`, never a bare `git reset`.

THREE HAZARDS, EACH MEASURED RATHER THAN IMAGINED:

1. A default that cannot be escaped is worse than no default, because it forces an author to either accept a wrong gate or bypass the tool. The explicit `-` path is not optional polish; V-01 case 3 must prove it works.
2. A default that REFUSES when it cannot resolve is worse still: it breaks the verb in every repo with no release record, which is what a fresh `aw install` produces. Review implemented that version and measured 10 test failures. V-01 case 4 is the guard.
3. A default applied to `--status done` manufactures an item the shipped exit-blocking checker rejects. Review drove it and got one `check.blocking-item-closed-without-gate`. The `done` skip and its V-01 evidence are what keep this child from creating the violation child 03 exists to eliminate.
