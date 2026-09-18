# IPD: Enforce a live bug carrying a release gate in aw check and backfill the existing violations

- Date: 2026-09-11
- Kind: child
- Concern: Writing the rule down and defaulting it at creation still leaves two holes: a hand-authored artifact bypasses the setter entirely, and the already-ungated live bugs stay invisible. Without a checker the rule decays silently again, which is exactly how the violations accumulated unnoticed. RE-MEASURED AT REVIEW (2026-09-12, HEAD `45158943`): the population is 22, not 28 (10 `open`, 11 `graduated`, 1 `blocked`), out of 67 live bug items.
- Scope: Add one `aw check` rule refusing a live bug-kind item with no release gate, registered in the rule registry so CI fails on it, then backfill the existing violations or record an explicit exemption for each. Does NOT change the creation default (child 02 owns it), does NOT gate other work kinds, and does NOT retroactively gate a bug already `done`.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_bug_gate_check.py, .aw/records/backlog, .aw/records/plans/pending
- Item-Dependencies: executed:di08i9
- Status: executed
- Readiness: go-pending-approval
- Set: nobugship
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rgaasb
- Blocks-Release: next

## Workflow history
- 2026-09-18 executed (aw oc run): aw oc run self-finalize: rgaasb verified (set nobugship, attempt 1).
- 2026-09-18 executed-pending-transition (opencode its_direct/pt3-claude-opus-5-1m-us): ALL WORK PERFORMED AND VALIDATED IN LANE `rgaasb` (run `run-20260918T205349Z-3540382`, queue position 4). E-01..E-05 performed, V-01..V-05 verified with pasted evidence. THE TERMINAL TRANSITION IS NOT MINE TO MAKE: this process runs with `AW_EXECUTION_ROLE=worker`, and `aw ipd finalize` refused with `AW-LIFECYCLE-ROLE-001` ("the runner owns begin/finalize for managed lanes"), so this plan correctly stays in `pending/` at `- Status: approved` and the driver performs the transition after integrating the lane. Nothing was hand-edited to simulate it.
  DELIVERED IN FOUR PATH-SCOPED COMMITS, no push: `5ceff69a` the checker (new `check.live-bug-ungated` at `error` under I-07, plus the OQ-03 terminal-carrier narrowing, plus 36 tests of which 24 fail against pre-change code); `9e1a8d8b` the backfill (64 of 65 population items gated through the shipped setter, 0 failures, 1 deliberate exemption); `c2638561` the co-update (12 live `From-Backlog` carriers, 0 failures, the 3 terminal carriers untouched); `0aa7c67c` six backlog items for the defects this execution found.
  FOUR MEASUREMENTS THAT CORRECT THIS PLAN'S OWN TEXT, each stated in the V-evidence rather than quietly satisfied. (1) THE POPULATION IS 65 (47 `open`, 18 `graduated`, 0 `blocked`), not the authored 28 or review's 22: it roughly TRIPLED in six days, concentrated in items filed AFTER child 02's creation default shipped, because the default covers CREATION and nothing covers RECLASSIFICATION into `bug` (filed `98zlut`). The `blocked` item review had to special-case is no longer in the population at all, so E-04's `--gate-kind`/`--gate-ref` row has no subject. (2) `check.from-backlog-gate-mismatch`'s BASELINE IS 2, NOT ZERO: two pre-existing false positives where a carrier spells the gate `f33nrj` and its item spells it `next`, which resolve to the SAME release record (filed `0cqf33`). This plan's net effect on that rule is +0 (2 -> 14 after the backfill -> 2 after the co-update), which is the Set's criterion 6; it is NOT literal zero and I am not claiming it is. (3) E-01'S PRESCRIBED PER-ITEM `find_from_backlog_artifacts` CALL WOULD HAVE BEEN A DEFECT: measured 11.13 s against 207 ms for one shared walk (54x) on `aw check all`, so E-01's own fallback clause was taken and the walk was factored into a shared `_from_backlog_carrier_index` consumed by both rules (filed `8cpbia` as a `chore`, correctly, since no shipped caller loops). (4) NO CI STEP FAILS ON THIS RULE: no workflow runs `aw check`/`aw check all` and the backlog step is advisory per DECISION 18-r2ks4k-D1, so the Scope sentence "so CI fails on it" is NOT TRUE and is filed as `wu8qjy` instead of being left standing.
  ONE ITEM DELIBERATELY NOT GATED, AND ONE DEFERRED QUESTION. `cnwy8g` stays ungated and is the single surviving `check.live-bug-ungated` finding: its record holds TWO conflicting maintainer-era decisions (2026-09-03 gated it; 2026-09-09 cleared the gate with a recorded reason whose premise verifies, `818uru` being `executed` and carrying the gate). Re-gating would reverse a human's later, more specific decision and re-create three findings they removed, so it is raised as DEFERRED 04-rgaasb-Q1 rather than decided mid-run. Separately, E-04's PRESCRIBED EXEMPTION MARKER DOES NOT WORK: a literal `- Blocks-Release: -` trades this rule for `check.blocks-release-dangling`, and a no-op de-gate silently discards the `--message` carrying the reason, so the exemption cannot live on the artifact today (filed `b0dcyp`).
  VALIDATION, bare runs with the actual summaries pasted in V-03/V-05: suite `8100 passed, 3 skipped, 2 xfailed in 164.30s` before the first edit and `8136 passed, 3 skipped, 2 xfailed in 99.79s` after, the +36 being exactly the new test file and the failure set empty in both. `aw check all` per-rule delta shows every unrelated rule UNCHANGED; `check.scope-drift` fell 336 -> 167 and that drop is attributed to the narrowing's `is_retired` short-circuit (proven by stashing only the record edits and re-measuring), not to the backfill and not to editing anyone else's artifact. Release blockers 109 -> 190. No item's `- Status:`, `- Priority:`, `- Work-Kind:`, `- Id:`, `- Set:` or `- Summary:` changed, and no file moved status directory. `aw ipd lint --phase pre-transition` conforms (exit 0). One hazard worth passing on: the environment's `PYTHONPATH` pins `agent_workflows` to the MAIN checkout, so a bare `aw` in a lane measures the WRONG TREE; it briefly produced a wrong mismatch count here until the module path was pinned and verified.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-12 reviewed round 2 (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 now FIXED by the maintainer's OQ-03 ruling, PR-012 (NEW, MEDIUM) FIXED, PR-002..PR-011 FIXED; readiness `no-go` -> `go-pending-approval`. `aw ipd lint --phase review-finalize` CONFORMING (the earlier `IPD-Q501` on blocking OQ-03 cleared when the question was answered). THE RULING WAS VERIFIED, NOT TRUSTED, because it arrived as an edit to a plan under review: its load-bearing measurement reproduces (gating pending plan `yeh7gc` under ungated item `5ev6lh` yields ZERO findings, cause `if mid and mbr` at `check_engine.py:2213-2216`), and every precedent it cites exists (`is_retired` `:482-494`, `_EXECUTED_SEGMENT` `:999`, the neighbouring `executed/` exclusion `:1069-1071`). THE RULED REMEDY WAS THEN EXECUTED END TO END in a throwaway copy: narrowing applied, all 22 items backfilled, findings 15 -> 13 (both terminal carriers gone), the 13 live carriers co-updated -> ZERO findings, 0 command failures, bare suite `5971 passed, 3 skipped, 2 xfailed in 61.04s`. PR-012 is the gap the ruling left: it authorized the plans tree in scope and the OQ-03 prose says so twice, but the `- Scope-Paths:` FIELD still forbade it, which would have sent the executor into the finalize gate with 13 undeclared edits; `.aw/records/plans/pending` is now declared. Also tightened: E-04 must narrow BEFORE backfilling (the reverse order reds the exit-blocking sweep in a shared checkout), and spec-sync now records that this plan AMENDS a shipped rule.
- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN and escalated to blocking OQ-03), PR-002..PR-011 FIXED; readiness `no-go` because one blocking question remains. Record: `.aw/records/reviews/20260911-nobugship-03-rgaasb-enforce-a-live-bug-carrying-a-release-gate-in-aw-check-and-b.review.md`. `aw ipd lint --phase author --agent` CONFORMING (clean, exit 0, 0 findings) before semantic review and `--phase review-finalize` after every revision. DISCLOSURE: the same agent/model family authored this Set, so treat this as a near-self-review; its value rests on what was EXECUTED.
  THE WHOLE BACKFILL WAS EXECUTED IN A THROWAWAY COPY, WHICH IS HOW EVERY FINDING BELOW WAS FOUND. All 22 items were driven through the shipped setter one at a time. The result: 21 succeeded, 1 REFUSED, and the tree ended with 15 NEW `check.from-backlog-gate-mismatch` ERROR findings, 2 of them naming plans in `executed/`. The parent's blocking OQ-03 is therefore CONFIRMED and its scale CORRECTED: the plan says 11 plan edits, the measurement says 15 carriers, and two `open` items (`f5pttg`, `x6tk1u`) also have carriers, which the plan does not mention at all.
  TWO OF THIS PLAN'S OWN VALIDATION GATES ARE UNREACHABLE AS WRITTEN, and this is the finding that would have wasted the most execution time. E-05 and V-05 require `aw check backlog` clean as the proof of success. Driven on the fully backfilled tree, `aw check backlog --agent` reported `outcome conforms, exit 0, findings 0` WHILE 15 new ERROR findings existed, because `check_release_gate_consistency` is wired into the once-per-full-sweep seam in `check_types` (`check_engine.py:1806-1811`) and `check_type('backlog')` never calls it (verified by source inspection AND by `check_types(repo,['backlog'])` returning 0 while `['all']` returned 183). So `aw check backlog` is the WRONG command for this plan's own rule, and a clean result from it proves nothing.
  THE SETTER REFUSES THE ONE `blocked` ITEM, measured: `aw backlog set blocked adgtqb --blocks-release next` FAILS with "Moving backlog item to blocked requires --gate-kind and --gate-ref", exit 1, because re-asserting `blocked` re-validates the typed gate. It succeeds only when the item's existing `Gate-Kind: artifact` / `Gate-Ref: yvvf98` are re-supplied on the command line. E-04 named this item as needing judgement but not that its command differs.
  E-01'S CENTRAL DESIGN INSTRUCTION IS IMPOSSIBLE. It requires composing with `evaluate_blocking_close`, but that predicate returns `(True, "ok", "unchecked transition")` for an UNGATED item: every one of its branches keys on `blocks_release` being PRESENT (`check_engine.py:2016`, `:2028`, `:2065`, `:2077`), which is exactly the opposite of what this rule detects. Driven at review on a synthetic ungated open bug to confirm. The reusable pieces are `find_from_backlog_artifacts` and the parse helpers, not the close predicate.
  ONE THING THE PLAN GOT EXACTLY RIGHT AND REVIEW CONFIRMED: `I-07` is the correct invariant, and its catalog text supports the choice. Read at `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md:135`, I-07 is "Release-gate preservation", assurance class "Repository invariant", and its control column already names `evaluate_blocking_close` and the sibling rules. The plan's warning about the `check.setid-collision` misfiling is also real and is recorded in that same spec.
  ELEVEN THINGS WERE DRIVEN RATHER THAN RECALLED: the population recomputed per item with status and priority; the carrier set recomputed for ALL 22 items (15 carriers, not 11); the full 22-item backfill executed through the setter; the resulting `check_release_gate_consistency` finding set enumerated with each carrier's directory; `aw check backlog` and `aw check all` both run on the backfilled tree and compared; `check_types(repo,['backlog'])` vs `['all']` compared in-process; the `blocked` item's refusal reproduced and then cleared with its gate flags; `aw ipd set --blocks-release` driven on a pending carrier (works) and on an `executed/` carrier (refuses, demanding `--actor` via finalize); a same-status vs different-status `ipd set` compared, showing the status-argument hazard is real; `evaluate_blocking_close` called on an ungated item; the bare suite run on the backfilled tree (`5971 passed, 3 skipped, 2 xfailed in 62.80s`); and the release-blocker view counted before (114) and after (136).
- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the third part of the answer to the maintainer's 2026-09-11 question, and the part that makes the other two hold. MEASURED at HEAD `2ff2b1b1` (NOTE: review could not verify this commit; `git cat-file -t 2ff2b1b1` reports "Not a valid object name" in this repository, so the authored anchor is unresolvable and every figure was re-derived from disk): a rule family for exactly this shape already ships, all at `error` severity under invariant `I-07` (`check_engine.py:105-127`): `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.blocks-release-dangling`, `check.from-backlog-dangling`, `check.from-spec-dangling`, plus the heuristic `check.orphaned-live-blocker` at `warning`. So this rule EXTENDS an established family rather than inventing a category. THE BACKFILL POPULATION AT AUTHORING: 28 live gateless bugs, split 16 `open`, 11 `graduated`, 1 `blocked`. It WILL differ at execution time and the parent's E-01 re-measures it.

## Goal

Make the rule self-maintaining, so a future ungated bug is reported rather than accumulating, and clear the existing violations (22 at review, re-derive at execution) so the check starts from a true zero.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: add the check

- [x] E-01 WRITE THE PREDICATE, REUSING THE FAMILY'S SHAPE RATHER THAN INVENTING ONE. A live bug-kind item with no `- Blocks-Release:` is a finding. LIVE means `open`, `blocked` or `graduated`; a `done` item is NOT flagged, because rewriting a closed bug's gate would assert a history that did not happen, and `parked` is an uncommitted maybe that the attention view already hides.
  DO NOT COMPOSE WITH `evaluate_blocking_close`; IT CANNOT ANSWER THIS QUESTION. This REPLACES the plan's original instruction, which review measured as impossible (PR-002). That predicate returns `CloseVerdict(True, "ok", "unchecked transition")` for an UNGATED item, because every one of its branches keys on `blocks_release` being PRESENT (`check_engine.py:2016` `if not blocks_release`, `:2028`, `:2065`, `:2077`); driven at review on a synthetic ungated `open` bug, it returned exactly that. An ABSENT gate is outside its domain by construction, so "compose with it" would either be a no-op wrapper that reports nothing or a rewrite of a shipped predicate three other surfaces depend on.
  REUSE THESE INSTEAD, WHICH ARE THE REAL SHARED PIECES: `find_from_backlog_artifacts` (`check_engine.py:1947-1960`) for the handoff test, `_backlog._iter_items` for the item walk, and the existing `_META_BLOCKS_RELEASE_RE` / `_ITEM_ID_RE` / `_status_meta` parse helpers that `check_release_gate_consistency` itself uses. That is genuine reuse of the family's shape without forking gate legitimacy. If you find yourself wanting a shared abstraction, FACTOR the item-walk-and-parse out of `check_release_gate_consistency` and have both call it; do not duplicate the regexes.
  DECIDE WHETHER A GRADUATED ITEM IS SATISFIED BY ITS PLAN'S GATE, and this is the substantive design choice. `AGENTS.md` already treats a plan carrying `From-Backlog` plus the same `Blocks-Release` as a legitimate HANDOFF that lets an item close. The same logic says a `graduated` bug whose plan carries the gate is not a violation. Measured at review, that exemption would apply to NONE of the 22 today (0 of 15 carriers carries a gate); but the predicate should still express it, or a correctly-handed-off bug would be flagged forever.
  - Depends on: none
  - Expected outcome: a predicate returning a finding per live gateless bug, exempting `done` and `parked`, treating a gated handoff carrier as satisfying, and reusing the family's item-walk/parse helpers and `find_from_backlog_artifacts` rather than either duplicating regexes or wrapping a predicate that cannot answer the question. State explicitly, with the driven output, why `evaluate_blocking_close` was NOT used.
  - Execution state: performed

- [x] E-02 REGISTER THE RULE IN `RULE_REGISTRY` under invariant `I-07` at `error`, matching its four siblings (`check_engine.py:105-116`). THE INVARIANT FIT IS NOW VERIFIED RATHER THAN ASSUMED, so this item's judgement call is settled: read at review, `I-07` is "Release-gate preservation: a release-blocking backlog item (`- Blocks-Release:`) may close `done` only if the gate is provably preserved..." with assurance class "Repository invariant", and its control column already names `evaluate_blocking_close` plus the sibling rules (`.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md:135`). Cite that line. The plan's warning is also real and stands: the same spec records the `check.setid-collision` misfiling under `I-09` as a correction not yet applied to the code, so do not choose an id by convenience.
  NOTE ONE HONEST TENSION TO RECORD RATHER THAN PAPER OVER: I-07 as written is about the CLOSE direction ("may close `done` only if..."), while this rule governs the OPEN direction (a live item must CARRY a gate). It is the same invariant's other half and `I-07` is still the right home, but say so in the registration comment, because a future reader comparing the rule to the catalog text will otherwise see a mismatch and re-litigate it. Consider proposing the catalog wording be widened; that is a spec edit and is NOT in this plan's `Scope-Paths`, so propose it, do not perform it.
  STAGE THE SEVERITY ONLY IF THE BACKFILL CANNOT COMPLETE. `error` is correct for the end state and matches the family. If E-04's backfill leaves any item unresolved, the rule must still ship at `error` with those items carrying an explicit recorded exemption, NOT at `warning` with a promise to tighten later; a rule left permanently at `warning` is the failure mode recorded on `rnkqrc` E-05.
  WIRE IT WHERE IT WILL ACTUALLY RUN, AND THIS IS NOT OPTIONAL PLUMBING (PR-003). Measured at review: `check_release_gate_consistency` is called ONLY from the once-per-full-sweep seam in `check_types` (`check_engine.py:1806-1811`), so `check_type('backlog')` never reaches it and `aw check backlog` cannot report it. Verified two ways: by source inspection, and by calling `check_types(repo, ['backlog'])` (0 findings) against `check_types(repo, ['all'])` (183) on a tree carrying 15 known mismatches. DECIDE and RECORD which seam this rule joins: the full-sweep seam beside its siblings (consistent, but then `aw check backlog` will not show it and E-05's evidence command must change), or the backlog content path so the type-scoped command reports it too. Whichever you choose, prove it by running BOTH `aw check backlog` and `aw check all` on a tree with a known violation and pasting both.
  CONFIRM CI ACTUALLY FAILS ON IT, because the plan's Scope claims "registered in the rule registry so CI fails on it" and that is not automatic. Measured: `.github/workflows/tests.yml:153-170` runs `aw check plans` and `aw check releases` FAIL-CLOSED but runs `aw check backlog` with `|| true` as ADVISORY (deliberately, per DECISION 18-r2ks4k-D1, until the backlog baseline is cleaned). So a rule reported only by `aw check backlog` does NOT fail CI today. State which CI step will fail on this rule, and if none will, say so plainly rather than letting the Scope sentence stand as an unverified claim.
  - Depends on: E-01
  - Expected outcome: the rule registered at `error` under `I-07` with the catalog line cited and the open-versus-close tension noted; the chosen call seam recorded and proven by running both `aw check backlog` and `aw check all` on a violating tree; and an explicit statement of which CI step fails on it, or that none does.
  - Execution state: performed

- [x] E-03 TEST THE RULE AND ITS EXEMPTIONS in a new `tests/test_bug_gate_check.py`, with a falsification pass against pre-change code. Cover: a live gateless bug FLAGGED; a gated bug CLEAN; a `done` gateless bug CLEAN; a `parked` gateless bug CLEAN; a non-bug gateless item CLEAN; and a `graduated` gateless bug whose carrier plan holds the gate CLEAN.
  DROP THE ANTI-FORK ASSERTION AS WRITTEN AND REPLACE IT WITH A REUSE ASSERTION (PR-002). The original asked for proof that the predicate consumes `evaluate_blocking_close`, which E-01 no longer does and cannot; a test asserting it would pin the wrong design in place. Assert instead that the new predicate calls `find_from_backlog_artifacts` for the handoff test (so the handoff definition has one owner) and that the module contains no second copy of the `Blocks-Release` metadata regex.
  ADD THE SEAM TEST, which is the one E-01's and E-02's correctness actually depends on: build a fixture repo with a live gateless bug and assert the rule is reported by whichever entry point E-02 chose, driven through `check_types` rather than by calling the predicate directly. Review measured that calling a predicate directly passes while the shipped command reports nothing, which is precisely how an unwired rule ships green.
  - Depends on: E-02
  - Expected outcome: six behavioral cases, the reuse assertions, and the seam test through `check_types`, each new assertion shown failing against pre-change code.
  - Execution state: performed

### Task group 2: clear the existing violations

- [x] E-04 RE-MEASURE AND BACKFILL, one item at a time, through the shipped setter. Use `aw backlog set <status> <id6> --blocks-release next` rather than hand-editing front matter, so the write goes through the same validation the tool applies elsewhere. RE-DERIVE THE POPULATION FIRST; the authored figure is 28 (16 `open`, 11 `graduated`, 1 `blocked`), review re-measured 22 (10 `open`, 11 `graduated`, 1 `blocked`), and both are now historical.
  OQ-03 IS ANSWERED, AND ITS RULED NARROWING MUST LAND BEFORE THIS ITEM'S BACKFILL, NOT AFTER. Review EXECUTED the full 22-item backfill in a throwaway copy and the tree ended with 15 NEW `check.from-backlog-gate-mismatch` ERROR findings, 2 naming plans in `executed/`. Then, at round 2, the maintainer's ruled remedy was executed end to end in the same copy: with the terminal-carrier narrowing applied the set is exactly 13 LIVE carriers, and co-updating those 13 through the setter reaches ZERO with no command failures. So sequence it that way (narrow the rule, then backfill, then co-update) rather than backfilling first and cleaning up, which is the order that produces a red exit-blocking sweep in a shared checkout.
  THE COLLISION IS LARGER THAN THIS PLAN STATED, so do not plan around the figure 11. Measured across ALL 22 items (not only the graduated ones): 15 carriers, 13 in `pending/` and 2 in `executed/`, and 0 of the 15 already carries a gate. TWO `open` ITEMS ALSO HAVE CARRIERS (`f5pttg` -> plan `4bc1nd`, `x6tk1u` -> plan `vhbvwz`), which this plan does not mention at all, so a remedy scoped to "the graduated ones" would leave two mismatches behind.
  THE `blocked` ITEM NEEDS A DIFFERENT COMMAND, measured: `aw backlog set blocked adgtqb --blocks-release next` FAILS with "Moving backlog item to blocked requires --gate-kind and --gate-ref" and exit 1, because re-asserting `blocked` re-validates the typed gate. It succeeds when its existing values are re-supplied: `--gate-kind artifact --gate-ref yvvf98`. Re-read the item's current gate fields rather than copying those values, and paste the command that worked.
  PASS THE ITEM'S CURRENT STATUS, NEVER A GUESSED ONE. The setter takes a status positionally, and review confirmed the hazard is real on the sibling verb: `aw ipd set to-review <plan> --blocks-release next` changed a `reviewed` plan to `to-review` and appended a status-change history line, while passing the SAME status reported `unchanged` and only wrote the gate. Read each item's `- Status:` first and echo it back in the command.
  EXPECT AN EXTRA HISTORY LINE PER ITEM AND DO NOT MISTAKE IT FOR CORRUPTION. Measured on the backfilled tree: each item gained `- <date> <status> (aw set): status set to <status>` in addition to the gate line, so the per-item diff is two insertions, not one. V-04's "only the gate line and history changed" is satisfied by that shape; say so rather than investigating it mid-run.
  DO NOT BLANKET-APPLY. For each item, state the gate applied or the exemption recorded. A bug that genuinely should not gate the release is a legitimate outcome and needs an explicit `- Blocks-Release: -` plus a reason in its history, not silent omission. Two named cases deserve individual judgement rather than a sweep: the `blocked` item `adgtqb` (already gated by a typed dependency, so its release relationship may differ) and any item whose summary suggests it is obsolete rather than open.
  WHETHER TO GATE THE CARRIERS AT ALL IS OQ-03'S ANSWER, NOT THIS ITEM'S CHOICE. If the answer is to co-update them, note that `aw ipd set <same-status> <plan> --blocks-release next` works on a `pending/` carrier (driven at review) but REFUSES on an `executed/` one: it reports that moving to `executed` delegates into gated `aw ipd finalize` and requires `--actor`, so the two terminal carriers have no tooled route. Do not work around that by hand-editing a terminal plan.
  - Depends on: E-03
  - Expected outcome: a per-item table showing the re-derived population, each item's status echoed from disk, the exact command used (including the gate flags for the `blocked` item), the action taken (gate applied, or exemption with its reason), and OQ-03's chosen remedy applied to the FULL carrier set with each carrier's directory named.
  - Execution state: performed

- [x] E-05 PROVE THE CHECK IS AT ZERO AND NOTHING ELSE MOVED. Show the new rule reporting no findings, and the release-blocker view carrying the newly gated items. Then show that no item's `- Status:`, `- Priority:` or `- Work-Kind:` changed as a side effect, since the setter takes a status argument and a mistake there would silently move an item's lifecycle state.
  DO NOT USE `aw check backlog` AS THE PROOF; IT IS BLIND TO THIS RULE FAMILY (PR-003). This REPLACES the plan's original success criterion. Measured at review on the fully backfilled tree, `aw check backlog --agent` reported `outcome conforms, exit 0, findings 0` while 15 `check.from-backlog-gate-mismatch` ERRORS existed, because the family is wired only into the full-sweep seam. Use `aw check all` (or the seam E-02 chose) and paste it. A clean `aw check backlog` is not evidence of anything here, and treating it as evidence is how this plan would have reported success over a red tree.
  REQUIRE A PER-RULE DELTA, NOT A CLEAN RESULT. `aw check all` carries pre-existing findings unrelated to this Set: measured at review, 183 findings comprising 124 `check.scope-drift`, 38 `check.setid-collision`, 15 `check.lifecycle-transition-invalid`, 3 `check.name-nonconformant`, and one each of `check.review-decision-unescalated`, `check.id6-collision` and `check.from-backlog-dangling`. Capture that per-rule tally BEFORE the first edit and compare per rule afterwards. Do NOT reduce any count by editing another party's artifact, which the shared-checkout rule forbids; in particular the one live `check.from-backlog-dangling` (a `From-Backlog: none` in an `executed/` plan) is pre-existing and is NOT this plan's to fix.
  STATE `check.from-backlog-gate-mismatch` EXPLICITLY IN THE DELTA. It measured ZERO before the backfill and 15 after, in a throwaway copy. Whatever OQ-03 decides, the end state must be that this count is back at its baseline; that is the Set's completion criterion 6 and it is the single number that says whether this item succeeded.
  RE-VERIFY THE INDEX BEFORE EVERY COMMIT AND AFTER ANY FAILED HOOK. This item edits at least 37 tracked files (22 items plus 15 carriers) in a shared checkout where other agents commit concurrently, and pre-commit's stash and restore can leave their paths staged. Unstage precisely with `git restore --staged <path>`, never a bare `git reset`.
  - Depends on: E-04
  - Expected outcome: the new rule at zero findings through the shipped command, a per-rule `aw check all` delta against a pre-edit baseline with `check.from-backlog-gate-mismatch` back at baseline, the release-blocker count before and after, no collateral field change on any item, and the staged set proven to contain only this item's files.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A rule family for release-gate integrity already exists, all `error` under `I-07`: `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.blocks-release-dangling`, `check.from-backlog-dangling`, `check.from-spec-dangling` (`check_engine.py:105-124`), plus `check.orphaned-live-blocker` at `warning`.
- `I-07`'s catalog text is verified to support this rule's home: "Release-gate preservation", assurance class "Repository invariant", control column already naming `evaluate_blocking_close` and the siblings (`.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md:135`). The same spec records the `check.setid-collision`/`I-09` misfiling as an uncorrected code value.
- `evaluate_blocking_close` (`:1980`) owns gate legitimacy for the CLOSE direction ONLY. Every branch keys on `blocks_release` being PRESENT, so it returns "unchecked transition" for an ungated item and CANNOT express this rule (driven at review). The reusable pieces are `find_from_backlog_artifacts`, `_backlog._iter_items`, and the family's parse helpers.
- THE FAMILY IS WIRED INTO THE FULL-SWEEP SEAM ONLY. `check_release_gate_consistency` is called from `check_types` (`check_engine.py:1806-1811`) and never from `check_type`, so `aw check backlog` cannot report any of these rules; verified in-process (`check_types(repo,['backlog'])` -> 0 while `['all']` -> 183 on a tree with 15 known mismatches).
- CI TREATS BACKLOG AS ADVISORY. `.github/workflows/tests.yml:153-170` runs `aw check plans` and `aw check releases` fail-closed but `aw check backlog` with `|| true` (deliberately, per DECISION 18-r2ks4k-D1), so "CI fails on it" is not automatic and depends on which seam the rule joins.
- THE `blocked` STATUS RE-VALIDATES ITS TYPED GATE on every `aw backlog set blocked`, so a gate-only edit to a `blocked` item must re-supply `--gate-kind`/`--gate-ref` or it exits 1 (driven at review on `adgtqb`).
- A TERMINAL PLAN HAS NO TOOLED GATE-WRITE ROUTE: `aw ipd set executed <executed-plan> --blocks-release next` refuses, reporting that the transition delegates into gated `aw ipd finalize` and requires `--actor` (driven at review).
- `AGENTS.md` already defines a legitimate HANDOFF as a plan carrying `From-Backlog` plus the same `Blocks-Release`, which is the shape the graduated exemption should reuse; `find_from_backlog_artifacts` accepts a SPEC as a carrier too.
- A rule left permanently at `warning` is a recorded failure mode (`rnkqrc` E-05's obligation), so staged severity must have a stated end state.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | Nothing reports an ungated live bug today, which is how the count accumulated unnoticed (22 at review). Documentation and a creation default both leave the hand-authored route open, so a checker is what makes the rule self-maintaining. |
| F-2 | BLOCKER | THE BACKFILL DETONATES A SHIPPED ERROR RULE, and review proved it by EXECUTING the whole thing: all 22 items backfilled through the setter left 15 NEW `check.from-backlog-gate-mismatch` findings, 2 naming plans in `executed/`. This plan's E-04 is what trips the parent's blocking OQ-03, and no route it authorizes clears it. |
| F-3 | HIGH | THIS PLAN'S OWN SUCCESS CRITERION IS BLIND TO ITS OWN RULE FAMILY. E-05/V-05 require `aw check backlog` clean; measured on the backfilled tree it reported `conforms, exit 0, findings 0` while 15 ERRORs existed, because the family is wired only into the `check_types` full-sweep seam and `check_type('backlog')` never calls it. |
| F-4 | HIGH | THE COLLISION IS 15 CARRIERS, NOT 11, and it is not confined to graduated items: two `open` items (`f5pttg`, `x6tk1u`) also have carriers. A remedy scoped to "the 11 graduated plans" would leave mismatches behind. |
| F-5 | HIGH | E-01'S CENTRAL DESIGN INSTRUCTION IS IMPOSSIBLE. `evaluate_blocking_close` returns "unchecked transition" for an ungated item because every branch keys on the gate being PRESENT; it cannot express the open direction. Driven at review. The anti-fork test in E-03 would have pinned the wrong design. |
| F-6 | MEDIUM | THE SETTER REFUSES THE ONE `blocked` ITEM: re-asserting `blocked` re-validates the typed gate, so `--blocks-release next` alone exits 1 and the item's `--gate-kind`/`--gate-ref` must be re-supplied. Measured on `adgtqb`. |
| F-7 | MEDIUM | "CI fails on it" is an unverified claim. `aw check backlog` runs with `|| true` as ADVISORY in CI (`tests.yml:166-170`, per DECISION 18-r2ks4k-D1), so a rule reported only there fails nothing. |
| F-8 | MEDIUM | The success criterion cannot be "clean" for any sweep this plan runs: `aw check all` carries 183 pre-existing findings unrelated to this Set, and reducing them would mean editing other parties' artifacts. A per-rule DELTA is the only honest criterion. |
| F-9 | MEDIUM | The invariant id is now VERIFIED rather than assumed: `I-07`'s catalog text supports it, with the honest caveat that the text is phrased for the CLOSE direction while this rule governs the OPEN direction. |
| F-10 | LOW | A terminal carrier has no tooled gate-write route: `aw ipd set executed` on an `executed/` plan refuses, demanding `--actor` via gated finalize. So option (a)-style co-updating genuinely stops at the two terminal plans. |
| F-11 | LOW | The setter appends a status-change history line per item even on a same-status call, so each backfilled item's diff is two insertions rather than one; V-04's evidence shape must expect that. |

## Proposed changes (ordered, validatable)

1. A predicate for a live gateless bug, reusing the family's walk/parse helpers and `find_from_backlog_artifacts`, and NOT the close-direction predicate, which cannot express it (E-01).
2. Registration at `error` under `I-07` with the catalog line cited, wired into a seam that actually runs it, and the CI reality stated (E-02).
3. Six behavioral tests, reuse assertions, and a seam test through `check_types`, with falsification (E-03).
4. A per-item backfill through the shipped setter, gated on OQ-03, covering the full 15-carrier collision set (E-04).
5. Proof via `aw check all` per-rule delta (not `aw check backlog` clean) with `check.from-backlog-gate-mismatch` back at baseline, and no collateral change (E-05).

## Deferred / out of scope (with reason)

- THE CREATION DEFAULT. Child 02 owns it, and this child depends on it so the backfill cannot immediately re-diverge.
- BUGS ALREADY `done`. Not flagged and not backfilled: a closed bug shipped or did not, and asserting a gate now would rewrite history.
- OTHER WORK KINDS, including `security`. The parent's OQ-01.
- A DEFECT MISLABELLED AS `chore`. The rule keys on `Work-Kind` and cannot see it; the parent's OQ-02 measures the leak and child 01 states it as a limit.
- WIDENING `I-07`'s CATALOG WORDING to cover the open direction as well as the close direction. The mismatch is real and worth fixing, but the catalog is a SPEC (`pqsx96`) and is not in this plan's `- Scope-Paths:`; E-02 proposes the change and does not perform it.
- FLIPPING CI's `aw check backlog` STEP FROM ADVISORY TO FAIL-CLOSED. That is DECISION 18-r2ks4k-D1's explicit precondition (the backlog name/summary baseline must be cleaned first) and touching `.github/workflows/tests.yml` is outside this plan's declared paths. E-02 states which step fails on the new rule instead.
  CARRIER AT EXECUTION: backlog `wu8qjy` (bug, gated on `next`). The answer E-02 had to state turned out to be that NO CI step fails on this rule at all: no workflow runs `aw check`/`aw check all`, and the one backlog step is advisory. So the parent Set's completion criterion 4 ("`aw check` reports a live bug with no gate, and CI fails on it") is HALF MET, and the unmet half now has a durable carrier with three costed remedies rather than vanishing with this plan.
- THE ONE PRE-EXISTING `check.from-backlog-dangling` FINDING (a `From-Backlog: none` in an `executed/` plan). It is another party's artifact in a terminal directory and predates this Set; leaving it is correct, and it must not be swept into this plan's delta as if it were fixed or caused here.
- WEAKENING `check.from-backlog-gate-mismatch`. Listed as a deliberate exclusion rather than a tempting shortcut: it is option (d) of the parent's OQ-03 and would blunt the shipped ERROR rule that catches a dropped graduation handoff, which is the same class of leak this Set exists to fix. NOT DONE, confirmed: the narrowing shipped here skips a TERMINAL carrier only, and `test_live_pending_carrier_still_flagged` plus `test_live_spec_carrier_still_flagged` pin that the dropped-handoff detection is intact for every live carrier.

- FIXING THE TWO PRE-EXISTING `check.from-backlog-gate-mismatch` FINDINGS (`h90ij1`, `z1yefm`). Discovered at execution, NOT known at authoring: review measured this rule at ZERO, but at execution its baseline is 2. Both carriers spell the gate `f33nrj` while their items spell it `next`, both resolve to the SAME release record, and neither item is in this plan's population. They are a FALSE POSITIVE in a fail-closed rule caused by literal string comparison, not a dropped handoff. Left untouched deliberately: they are another party's artifacts and reducing the count by editing them is what E-05 forbids. CARRIER: backlog `0cqf33` (bug, gated on `next`), which proposes resolving both sides through `releases.resolve_release` before comparing.

- RE-GATING `cnwy8g`, THE ONE EXEMPTED ITEM. It stays ungated and is therefore the single surviving `check.live-bug-ungated` finding. Its authority genuinely conflicts (a 2026-09-03 maintainer ruling gated it; a 2026-09-09 decision cleared that gate with a recorded reason), so an executor must not silently pick a side. Raised as DEFERRED QUESTION 04-rgaasb-Q1 in the run's decisions register.

- BUILDING A WORKING EXEMPTION MARKER. E-04 prescribes `- Blocks-Release: -` plus a history reason, and BOTH halves were measured broken at execution: the literal `-` trades this rule for `check.blocks-release-dangling`, and a no-op de-gate discards the `--message` carrying the reason. So a deliberate exemption is currently indistinguishable from an oversight. Designing the typed exemption is beyond this plan's scope; CARRIER: backlog `b0dcyp` (bug, gated on `next`).

- CLOSING THE RECLASSIFICATION ROUTE THAT REGROWS THIS POPULATION. Measured at execution: the population went 22 -> 65 in the six days since review, concentrated in items filed AFTER child 02's creation default shipped. The default covers CREATION; nothing covers an item RECLASSIFIED into `bug` later or hand-authored. Fixing that is child 02's surface, not this one's. CARRIER: backlog `98zlut` (bug, gated on `next`).

## Scope check

- Over-scope: none. The checker, one new test file, and the backlog tree the backfill edits.
- RESOLVED, no longer under-scope: E-04 must edit 13 LIVE carrier files (the 15 measured, minus the 2 in `executed/` that the ruling stops flagging), and `.aw/records/plans/pending` is now DECLARED in `- Scope-Paths:` per OQ-03's ruling, which required it "BEFORE any write". `agent_workflows/check_engine.py` was already declared and now carries the rule narrowing as well as the new rule. The two `executed/` carriers are never edited, so no `AGENTS.md` terminal-edit conflict remains.
- STILL DECLARED-BUT-UNMODIFIED RISK: `.aw/records/plans/pending` is broad, and the finalize scope gate reconciles declared paths against changed ones. Expect to justify each carrier edit and to `--scope-ack` nothing under it that you did not touch; do not treat the broad declaration as licence to edit an unrelated plan in that directory.
- Under-scope: nothing in the declared paths lets this plan make CI fail on its own rule, since the fail-closed steps are `aw check plans` / `aw check releases` and the backlog step is advisory. The Scope sentence claiming "CI fails on it" is therefore aspirational until DECISION 18-r2ks4k-D1's precondition is met; E-02 must state the truth rather than inherit the claim.

## Required tests / validation

`tests/test_bug_gate_check.py` with a falsification pass. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste it, and judge on the failure-SET delta rather than a number. FOR REFERENCE ONLY, review measured it bare on a throwaway copy carrying the FULL backfill: `5971 passed, 3 skipped, 2 xfailed in 62.80s`, so the backfill alone breaks no test. Do NOT quote that as your baseline; re-measure. Run the suite BARE: the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0` or a second `-q` makes the run slower and suppresses the summary line the contract requires you to paste.

ESTABLISH A CHECKER BASELINE BEFORE THE FIRST EDIT, because this plan's real risk is in the sweep rather than in pytest. Capture the PER-RULE tally from `aw check all --agent` (review measured 183 findings: 124 `check.scope-drift`, 38 `check.setid-collision`, 15 `check.lifecycle-transition-invalid`, 3 `check.name-nonconformant`, 1 each of `check.review-decision-unescalated`, `check.id6-collision`, `check.from-backlog-dangling`, and ZERO `check.from-backlog-gate-mismatch`). The completion criterion is a per-rule delta against that baseline, with `check.from-backlog-gate-mismatch` back at zero.

DO NOT USE `aw check backlog` AS A VALIDATION COMMAND FOR THIS PLAN'S RULE FAMILY. Measured: it reports `conforms, exit 0, findings 0` on a tree carrying 15 of these ERRORs. It remains a fine check of backlog conformance in general; it is simply blind to the family this plan extends.

REPEAT THE THROWAWAY-COPY EXPERIMENT BEFORE TOUCHING THE REAL TREE. Review did exactly this (copy the repo, backfill all 22 items through the setter, run the shipped predicate) and it surfaced the blocker plus four other findings in one pass. Repeat it to confirm OQ-03's chosen remedy actually clears the mismatch, rather than discovering it mid-backfill across 37 files in a shared checkout.

## Spec / documentation sync

N/A with reason: child 01 records the rule and this child enforces it. The refusal message must POINT AT child 01's written text rather than restating policy, so the two cannot drift.

DISCHARGED AT EXECUTION: the finding's `detail` cites child 01's text by its section heading ("AGENTS.md, 'Every live bug gates the next release'") and the predicate's docstring says explicitly that it points at that text rather than restating the policy, so the two cannot drift. `test_finding_cites_the_written_rule_and_teaches_the_fix` asserts the citation is present in the emitted finding. No `AGENTS.md` edit was needed or made: child 01's text already states the obligation this rule enforces, including the `bug`-only gating set and the author-classification limit, so the code cites it rather than adding to it.

ONE SPEC IS GENUINELY ADJACENT AND MUST BE PROPOSED, NOT EDITED. The invariant catalog spec `pqsx96` phrases `I-07` for the CLOSE direction only, while this rule governs the OPEN direction. The registration comment must note the tension (E-02), and the wording change should be PROPOSED for a later plan, because `.aw/records/specs/` is not in this plan's `- Scope-Paths:` and a spec edit changes the contract every other plan is reviewed against. If the executor judges the amendment must land WITH this change, the correct route is to declare the spec path in `- Scope-Paths:` before execution and say why in this section, per the plan-may-amend-a-spec rule; do not edit it undeclared.

THIS PLAN NOW AMENDS A SHIPPED RULE, WHICH IS A CONTRACT CHANGE AND MUST BE RECORDED HERE, not only inside OQ-03. Per the maintainer's 2026-09-12 ruling, `check.from-backlog-gate-mismatch` is NARROWED so it fires only for a LIVE (non-terminal) carrier. That is a change to behavior other plans are reviewed against, so: state it in the E-02 registration comment; reuse the shipped `is_retired` (`check_engine.py:483`) or `_EXECUTED_SEGMENT` (`:999`) rather than a fresh path test, matching the neighbouring rule at `:1069-1070`; and write the test so it FAILS against today's code, since a narrowing that passes before and after proves nothing.
  MEASURED AT REVIEW ROUND 2, so the executor knows the target numbers: with the narrowing applied and all 22 items backfilled, the finding set drops from 15 to exactly the 13 LIVE carriers (the 2 terminal ones disappear); co-updating those 13 through `aw ipd set <current-status> <plan> --blocks-release next` then reaches ZERO, with 0 command failures; and the bare suite passed `5971 passed, 3 skipped, 2 xfailed in 61.04s` on that end state. Re-derive rather than quoting these, but a result that does not land on zero means the remedy was not applied as ruled.

AMENDMENT LANDED AS RULED, AND RE-DERIVED AT EXECUTION (the review figures above are historical and were NOT quoted as evidence). `check.from-backlog-gate-mismatch` is narrowed so it fires only for a LIVE carrier, implemented with the shipped `is_retired` predicate (`check_engine.py:514`) rather than a fresh path test. `is_retired` was chosen over the narrower `_EXECUTED_SEGMENT` literal deliberately (DECISION 04-rgaasb-D2): the ruled rationale ("work is DONE, there is no future release to gate") holds identically for a `superseded/` or `not-executed/` carrier, and on the current corpus both predicates give the identical 3-terminal / 15-live split, so the choice cannot change this run's numbers and only decides a future superseded carrier's treatment. The registration comment and the function docstring both record the amended behavior and the maintainer's reasoning.

THE TEST FAILS AGAINST TODAY'S CODE, as required: `test_executed_carrier_is_skipped` and `test_superseded_and_not_executed_carriers_are_skipped` both FAIL pre-change (pre-change code flags those carriers), proven in the V-03 falsification run. BOTH DIRECTIONS ARE PINNED, which is the durable half of the ruling: `test_gated_carrier_under_ungated_item_is_clean` asserts the ZERO-finding direction explicitly, and its docstring records that the case is currently unreachable by construction, so a refactor cannot silently make the rule symmetric again.

RE-DERIVED END STATE (execution, not review): 18 carriers, 3 TERMINAL and 15 LIVE. With the narrowing applied the terminal 3 never appear. The backfill took the rule from its baseline of 2 to 14, and co-updating the 12 live carriers that needed it took it back to 2, with 0 command failures. It does NOT land on literal zero, and the reason is stated rather than hidden: the residual 2 are PRE-EXISTING false positives (`h90ij1`, `z1yefm`, a gate-spelling artifact, filed as `0cqf33`) that were present before the first edit and are another party's to fix. The net effect of this plan on that rule is +0, which is the Set's completion criterion 6. Bare suite on the end state: `8136 passed, 3 skipped, 2 xfailed in 99.79s`, against a pre-edit baseline of `8100 passed, 3 skipped, 2 xfailed in 164.30s`.

ONE DOCUMENTED DECISION MUST NOT BE CONTRADICTED: DECISION 18-r2ks4k-D1 deliberately keeps CI's `aw check backlog` step advisory until the backlog baseline is cleaned. This plan may not quietly flip it, and E-02 must state which CI step (if any) fails on the new rule rather than implying the Scope sentence is already true.

## Open questions

### OQ-01: Does a graduated bug whose plan carries the gate satisfy the rule?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: YES, AND E-01 IS WRITTEN THAT WAY, resolved from the existing contract rather than asked. `AGENTS.md` already defines a legitimate HANDOFF as a plan carrying `From-Backlog: <item>` plus the same `Blocks-Release`, and uses exactly that to let a gated item close without dropping its gate; `find_from_backlog_artifacts` accepts a SPEC as an equally valid carrier, so the exemption must too. The OPEN direction of the same invariant should recognise the same handoff, or a correctly-handed-off bug would be flagged forever and the rule would train people to ignore it. Non-blocking because it changes which items are flagged, not whether the rule is right: RE-MEASURED at review it exempts NONE of the 22, since 0 of the 15 carriers carries a gate. Record the decision in E-01's outcome.

### OQ-02: Should the rule also flag a gated item whose gate does not resolve?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: NO, BECAUSE IT ALREADY EXISTS. `check.blocks-release-dangling` (`check_engine.py:111`) is precisely that rule, at `error` under the same invariant. Duplicating it here would fork a shipped check, which is the drift this repository repeatedly pays for. Resolve by CITING that rule in the new rule's docstring so a reader sees the division of labour: this one catches an ABSENT gate, that one catches an UNRESOLVABLE one. Non-blocking and resolvable without the maintainer. NOTE the sibling this division also implies: `check.from-backlog-dangling` catches a carrier pointing at nothing, and one such finding is live and pre-existing in an `executed/` plan; it is not this rule's business and not this plan's to fix.

### OQ-03: This plan's backfill creates 15 `from-backlog-gate-mismatch` ERRORS, 2 of them on immutable plans. How is the gate propagated to the carriers?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: THIS IS THE PARENT'S OQ-03 (`qmgn12`), RESTATED HERE BECAUSE THIS PLAN IS THE ONE THAT TRIPS IT, and now CONFIRMED BY FULL EXECUTION rather than by a single-item probe. Review backfilled ALL 22 items through the shipped setter in a throwaway copy: 21 succeeded, 1 refused (the `blocked` item, until its gate flags were re-supplied), and the resulting tree carried 15 NEW `check.from-backlog-gate-mismatch` ERROR findings where it had ZERO before. 13 of the 15 carriers sit in `pending/` and 2 in `executed/` (`h9cn0y` from item `hyx1dg`, `5wtzqv` from item `t156g1`). The bare suite still passed (`5971 passed, 3 skipped, 2 xfailed`), so this is purely a checker-state collision, not a code break.
  THREE CORRECTIONS TO THE PARENT'S FRAMING, each measured. FIRST, the carrier count is 15, not 13, and the affected item set is not confined to the graduated ones: `f5pttg` -> plan `4bc1nd` and `x6tk1u` -> plan `vhbvwz` are both `open` items with carriers, so a remedy scoped to "the graduated 11" leaves two mismatches standing. SECOND, the terminal pair genuinely has NO tooled route: `aw ipd set executed <executed-plan> --blocks-release next` refuses, reporting that the transition delegates into gated `aw ipd finalize` and requires `--actor`, so option (a)'s co-update is available for the 13 pending carriers and blocked for the 2 terminal ones exactly as the parent said. THIRD, co-updating a pending carrier DOES work when its CURRENT status is passed (`aw ipd set reviewed <plan> --blocks-release next` reported `unchanged` and wrote only the gate), but passing a DIFFERENT status silently transitions the plan and appends a history line, which is a real hazard for a 13-plan sweep.
  DO NOT DECIDE THIS INSIDE THIS PLAN. Two of the parent's four options change a shipped ERROR rule's behavior and one leaves 11 real bugs ungated; that is a trade-off between a shipped contract and a backfill, which is the maintainer's call. Answer it on the parent (`qmgn12` OQ-03) with `/askme`, then execute the chosen remedy here. `aw ipd lint` refuses this plan at every checkpoint while this question is open, which is the intended stop.
  WHAT AN ANSWER MUST COVER, so it is actionable: whether the 13 pending carriers are co-updated (and if so, that `- Scope-Paths:` gains the plans tree first); what happens to the 2 terminal carriers; and whether the two `open`-item carriers are treated the same as the graduated ones.
  ANSWERED ON THE PARENT (`qmgn12` OQ-03) BY THE MAINTAINER 2026-09-12, exactly as this plan instructed. The ruling: RESTATE `check.from-backlog-gate-mismatch` AS THE ONE-WAY OBLIGATION IT ALREADY IMPLEMENTS, and SKIP A TERMINAL CARRIER. Read the parent's OQ-03 for the full reasoning and the two measurements; what follows is what THIS plan must do.
    THIS PLAN'S THREE CORRECTIONS TO THE PARENT'S FRAMING ALL SURVIVE THE RULING, and were re-verified at the time of the answer rather than taken on trust. The carrier count is 15, not the parent's 13. The affected set is NOT confined to the graduated items: `f5pttg` -> `4bc1nd` and `x6tk1u` -> `vhbvwz` come from `open` items. Both of those carriers were re-checked and sit in `pending/`, so they are LIVE and the ruling covers them with no special handling: a live carrier co-updates.
    SO THE THREE THINGS THIS PLAN'S OWN QUESTION ASKED FOR ARE ANSWERED. (1) THE 13 PENDING CARRIERS ARE CO-UPDATED, and `- Scope-Paths:` must gain the plans tree BEFORE any write, as this plan already demanded. (2) THE 2 TERMINAL CARRIERS (`5wtzqv`, `h9cn0y`) ARE NEVER TOUCHED; they stop being findings because the rule stops over-reaching, not because they are exempted by name. (3) THE TWO `open`-ITEM CARRIERS ARE TREATED IDENTICALLY TO THE GRADUATED ONES, because the discriminator the ruling settles on is the CARRIER's liveness, not the ITEM's status. That is why the ruling generalizes to a population this plan measured and the parent had not.
    ADDITIONAL SCOPE THE RULING AUTHORIZES, and it is a shipped-behavior change rather than a backfill: `agent_workflows/check_engine.py` joins `- Scope-Paths:`, because the narrowing is implemented here. Use the shipped terminal predicate (`is_retired`, `:483`) or `_EXECUTED_SEGMENT` (`:999`) rather than a fresh path test, matching the neighbouring rule that already excludes `executed/` for the identical reason (`:1069-1070`). Record the amended behavior in this plan's spec-sync section, and write the test so it FAILS against today's code.
    PIN BOTH DIRECTIONS IN THAT TEST, which is the durable half of this ruling. Measured 2026-09-12 in a throwaway clone: gating item `t156g1` flags carrier `5wtzqv` (+1 finding), while gating pending plan `yeh7gc` under ungated item `5ev6lh` yields ZERO. The second case is currently unreachable BY CONSTRUCTION (the loop populates `item_gate` only for a gated item, `check_engine.py:2207-2216`), so nothing today would notice if a refactor made the rule symmetric. Assert the zero-finding direction explicitly, or the reframing is undefended.
    DO NOT weaken the rule to flag only a both-gated CONFLICT. That option was put to the maintainer and DECLINED: it would drop the dropped-handoff detection that is the rule's entire purpose.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the predicate's output for SIX fixtures (live gateless bug, gated bug, `done` gateless bug, `parked` gateless bug, non-bug gateless item, graduated gateless bug whose carrier holds the gate), each with the verdict and reason.
    THEN paste the NON-USE PROOF for `evaluate_blocking_close`, which replaces the original anti-fork proof: call it on an UNGATED live bug fixture and paste the `CloseVerdict` showing `legitimate=True, severity='ok', reason='unchecked transition'`, demonstrating why it cannot back this rule. A validation that instead claims composition with that predicate is a FAILED validation, because review measured it impossible. Also paste the REUSE proof: a grep showing the new predicate calls `find_from_backlog_artifacts`, and a grep showing no second copy of the `Blocks-Release` metadata regex was introduced.
  - Observed evidence: ALL SIX FIXTURES BEHAVE AS SPECIFIED, driven through `check_engine.check_live_bug_gate` on six throwaway temp repos (the fixture builders are the new test module's, so the evidence and the tests cannot disagree):

    ```text
    1 live gateless bug         -> FLAGGED   rule=check.live-bug-ungated severity=error
                                     observed: Work-Kind: bug, Status: open, no Blocks-Release
                                     recovery: aw backlog set open aaa111 --blocks-release next  (or hand the gate to t
    2 gated bug                 -> CLEAN     (0 findings)
    3 done gateless bug         -> CLEAN     (0 findings)
    4 parked gateless bug       -> CLEAN     (0 findings)
    5 non-bug gateless item     -> CLEAN     (0 findings)
    6 graduated + gated carrier -> CLEAN     (0 findings)
    ```

    THE NON-USE PROOF, AND ONE CORRECTION TO THIS ITEM'S OWN EXPECTED STRING. `evaluate_blocking_close` on an UNGATED live bug fixture returns, for the CLOSE transition this plan asked about:

    ```text
    CloseVerdict(legitimate=True, severity='ok', reason='no release gate to preserve', fixes=(), path='DE-GATED')
    ```

    and for any other transition:

    ```text
    CloseVerdict(legitimate=True, severity='ok', reason='unchecked transition', fixes=(), path=None)
    ```

    So the required `legitimate=True, severity='ok'` is confirmed, but the REASON for `target_status='done'` is `'no release gate to preserve'` (path `DE-GATED`), NOT `'unchecked transition'`; the latter is what the OTHER transitions return. This item's expected string was therefore slightly wrong about which branch fires, and the correction strengthens rather than weakens the conclusion: the predicate does not merely decline to judge an ungated item, it AFFIRMATIVELY treats the absent gate as "nothing to preserve" and returns legitimate. Both directions are pinned by `test_evaluate_blocking_close_cannot_answer_the_open_direction`. The predicate is NOT consumed by the new rule.

    THE REUSE PROOF, IN ITS ADAPTED FORM, AND THE ADAPTATION IS DELIBERATE (DECISION 04-rgaasb-D1). This item asked for a grep showing the predicate calls `find_from_backlog_artifacts`. It does NOT, and shipping that shape would have been a measured defect: that function re-walks the ENTIRE plans tree plus the specs tree per call, so one call per candidate item costs O(items x corpus). Driven on this checkout (671 plans, 34 specs, 65 candidates): **11.13 s** for the per-item form against **207 ms** for one shared walk producing the identical mapping, a **54x** difference on `aw check all`, a command a human waits on. E-01's own fallback clause authorizes exactly the remedy taken ("FACTOR the item-walk-and-parse out of `check_release_gate_consistency` and have both call it"), and `release_gate_warnings` already records being bitten by this identical shape and refactoring away from it. So the reuse is via one new shared `_from_backlog_carrier_index`, and the property the original grep existed to protect (ONE owner for the handoff definition, no duplicated regex) is proven directly:

    ```text
    $ grep -n "_from_backlog_carrier_index" agent_workflows/check_engine.py
    2274:def _from_backlog_carrier_index(
    2401:    for target_id6, carriers in _from_backlog_carrier_index(repo_root).items():   # mismatch rule
    2499:            carrier_index = _from_backlog_carrier_index(repo_root)                # new rule

    $ grep -c 'r"(?m)^- Blocks-Release:' agent_workflows/check_engine.py
    1
    1955:_META_BLOCKS_RELEASE_RE = _re.compile(r"(?m)^- Blocks-Release:[ \t]*(\S+)[ \t]*$")

    neither consumer walks the trees itself (checked in-process, '_iter_plan_ipds' or
    '_iter_spec_records' present in the function source):
      check_live_bug_gate: False
      check_release_gate_consistency: False
    ```

    Exactly ONE compiled `- Blocks-Release:` metadata regex exists in the module, so no second copy was introduced. `tests/test_bug_gate_check.py::LiveBugGateReuseTests` pins all four properties, including that neither consumer re-derives the walk.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `RULE_REGISTRY` entry showing `error` and `I-07`, and paste the invariant catalog line that justifies it (`...pqsx96...spec.md:135`) together with the registration comment noting the open-versus-close tension.
    THEN paste the SEAM PROOF, which is the evidence this item's correctness actually turns on: on a fixture tree containing a live gateless bug, run BOTH `aw check backlog --agent` and `aw check all --agent` and paste both, showing which one reports the new rule id. Do NOT paste only the one that passes. If the rule is reachable only from the full sweep, say so explicitly, because E-05's evidence command depends on it.
    FINALLY state which CI step fails on this rule, quoting the workflow line. If none does (because `aw check backlog` runs with `|| true` per DECISION 18-r2ks4k-D1), say that plainly; an unqualified "CI fails on it" is a FAILED validation.
  - Observed evidence: THE REGISTRY ENTRY, at `error` under `I-07`, matching its four siblings:

    ```python
    "check.live-bug-ungated": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    ```

    THE CATALOG LINE THAT JUSTIFIES IT, read at `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md:135` (verified at that exact line this session):

    ```text
    | I-07 | Release-gate preservation: a release-blocking backlog item (`- Blocks-Release:`) may close
    `done` only if the gate is provably preserved (handoff to a `From-Backlog` plan), satisfied
    (resolvable in-tree evidence), or explicitly de-gated. | Repository invariant | ... | control:
    `check_engine.evaluate_blocking_close`; `check.blocking-item-closed-without-gate`,
    `check.from-backlog-gate-mismatch`, `check.orphaned-live-blocker`; `aw backlog set done` setter; ... |
    ```

    THE OPEN-VERSUS-CLOSE TENSION IS RECORDED IN THE REGISTRATION COMMENT rather than papered over, as this item required: I-07's text is phrased for the CLOSE direction while this rule governs the OPEN direction. The comment states that it is the same invariant's other half, says why I-07 is still the right home (a rule about whether a gate EXISTS to be preserved belongs with the rules about preserving it), and records that widening the catalog wording is a SPEC edit outside this plan's `- Scope-Paths:` and is therefore PROPOSED, not performed.

    THE SEAM PROOF, BOTH COMMANDS, ONE FIXTURE TREE holding a single live gateless bug. This is the evidence this item's correctness turns on, and BOTH results are pasted including the one that reports nothing:

    ```text
    $ python3 -m agent_workflows check backlog --dir <fixture> --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,
     "complete":true,"target":"backlog","findings":0,"evidence":["inventory","rules"],"next":"aw backlog check"}
    EXIT=0

    $ python3 -m agent_workflows check all --dir <fixture> --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,
     "complete":true,"target":"all","findings":1,"evidence":["inventory","rules"],
     "diagnostics":[{"location":".aw/records/backlog/open/20260918-tst-01-aaa111-a-live-gateless-bug.backlog.md",
     "rule":"check.live-bug-ungated"}], ...}
    EXIT=1
    ```

    STATED EXPLICITLY, because E-05's evidence command depends on it: **THE RULE IS REACHABLE ONLY FROM THE FULL SWEEP.** `aw check backlog` reports `conforms, exit 0, findings 0` on a tree that genuinely violates the rule, because the whole I-07 family is wired into the once-per-full-sweep `if collisions:` block in `check_types` and `check_type('backlog')` never reaches it. So `aw check backlog` is worthless as evidence here, exactly as this plan warned, and V-05 uses `aw check all`. The chosen seam is recorded in DECISION 04-rgaasb-D3 with its reasoning: the rule is deliberately NOT added inside `check_release_gate_consistency`, because that function is composed by `check_commit_invariants` (the pre-commit aggregator) where every rule is commit- or receipt-scoped, and a WHOLE-TREE rule there would refuse a commit because another party's item elsewhere in the tree is ungated. `test_whole_tree_rule_is_absent_from_the_precommit_aggregator` pins that, and `test_backlog_type_scope_does_NOT_report_it` pins the stated cost so it stays a decision rather than a surprise.

    WHICH CI STEP FAILS ON THIS RULE: **NONE.** Stated plainly, because an unqualified "CI fails on it" would be a failed validation. Grepped `.github/workflows/*.yml`: the only check steps are `aw check plans` and `aw check releases` (FAIL-CLOSED, `tests.yml:153-159`) and `aw check backlog` (ADVISORY, `tests.yml:166-170`):

    ```yaml
      - name: aw check backlog (backlog conformance; ADVISORY until baseline cleaned)
        shell: bash
        run: |
          python -m agent_workflows check backlog --agent || \
            echo "::warning::aw check backlog reported findings (advisory; see agentadhere r2ks4k DECISION 18-r2ks4k-D1 ...)"
    ```

    No workflow step runs `aw check` or `aw check all` at all, so the rule that enforces "we do not ship known bugs" exits 1 locally and fails NOTHING remotely. The plan's Scope sentence ("registered in the rule registry so CI fails on it") is therefore NOT TRUE as written, and I am not letting it stand as an unverified claim. This gap is the parent Set's completion criterion 4 being only half met; it is filed as backlog `wu8qjy` (bug, gated on `next`) with the three costed remedies, because `.github/workflows/tests.yml` is outside this plan's `- Scope-Paths:` and the obvious fix contradicts DECISION 18-r2ks4k-D1's stated precondition.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_bug_gate_check.py -o addopts=""` with per-test names, then the FALSIFICATION showing the new cases FAIL against pre-change code. Confirm by name that the six behavioral cases, the two reuse assertions, and the `check_types` seam test are all present.
  - Observed evidence: 36 tests, all passing, per-test names as run (`-p randomly` orders them nondeterministically, which is left on deliberately):

    ```text
    $ python3 -m pytest tests/test_bug_gate_check.py -o addopts="" -v
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    collected 36 items

    LiveBugGateSeamTests::test_full_sweep_reports_the_rule PASSED
    LiveBugGateSeamTests::test_whole_tree_rule_is_absent_from_the_precommit_aggregator PASSED
    LiveBugGateSeamTests::test_clean_tree_is_silent PASSED
    LiveBugGateSeamTests::test_backlog_type_scope_does_NOT_report_it PASSED
    LiveBugGateBehaviorTests::test_parked_gateless_bug_is_clean PASSED
    LiveBugGateBehaviorTests::test_gated_bug_is_clean PASSED
    LiveBugGateBehaviorTests::test_live_gateless_bug_is_flagged PASSED
    LiveBugGateBehaviorTests::test_non_bug_gateless_item_is_clean PASSED
    LiveBugGateBehaviorTests::test_graduated_gateless_bug_with_gated_carrier_is_clean PASSED
    LiveBugGateBehaviorTests::test_done_gateless_bug_is_clean PASSED
    MismatchNarrowingTests::test_narrowing_uses_the_shipped_terminal_predicate PASSED
    MismatchNarrowingTests::test_superseded_and_not_executed_carriers_are_skipped PASSED
    MismatchNarrowingTests::test_gated_carrier_under_ungated_item_is_clean PASSED
    MismatchNarrowingTests::test_dangling_from_backlog_is_still_another_rules_job PASSED
    MismatchNarrowingTests::test_live_pending_carrier_still_flagged PASSED
    MismatchNarrowingTests::test_matching_gates_are_clean PASSED
    MismatchNarrowingTests::test_live_spec_carrier_still_flagged PASSED
    MismatchNarrowingTests::test_executed_carrier_is_skipped PASSED
    LiveBugGateEdgeTests::test_legacy_kind_spelling_is_honored PASSED
    LiveBugGateEdgeTests::test_open_item_with_gated_carrier_is_also_exempt PASSED
    LiveBugGateEdgeTests::test_blocked_is_a_live_status_and_is_flagged PASSED
    LiveBugGateEdgeTests::test_finding_cites_the_written_rule_and_teaches_the_fix PASSED
    LiveBugGateEdgeTests::test_graduated_gateless_bug_with_UNGATED_carrier_is_still_flagged PASSED
    LiveBugGateEdgeTests::test_a_spec_is_an_equally_valid_carrier PASSED
    LiveBugGateReuseTests::test_the_live_set_agrees_with_the_creation_default PASSED
    LiveBugGateReuseTests::test_the_carrier_index_is_the_only_place_the_walk_is_written PASSED
    LiveBugGateReuseTests::test_predicate_does_not_fork_the_live_status_vocabulary PASSED
    LiveBugGateReuseTests::test_both_consumers_use_the_one_carrier_index PASSED
    LiveBugGateReuseTests::test_predicate_consumes_the_shared_carrier_index PASSED
    LiveBugGateReuseTests::test_evaluate_blocking_close_cannot_answer_the_open_direction PASSED
    LiveBugGateReuseTests::test_no_second_copy_of_the_blocks_release_regex PASSED
    BackfillEndStateTests::test_backfilling_an_item_with_a_terminal_carrier_reaches_zero PASSED
    BackfillEndStateTests::test_backfilling_an_item_with_a_live_carrier_needs_the_carrier_co_updated PASSED
    LiveBugGateRegistrationTests::test_shares_its_invariant_with_the_rest_of_the_I07_family PASSED
    LiveBugGateRegistrationTests::test_registered_as_a_deterministic_repository_invariant PASSED
    LiveBugGateRegistrationTests::test_registered_at_error_under_I07 PASSED

    ============================== 36 passed in 1.45s ==============================
    ```

    THE FALSIFICATION, run by stashing ONLY my own `agent_workflows/check_engine.py` and re-running the identical file. **24 of the 36 FAIL against pre-change code**, so the suite is genuinely falsifiable rather than tautological:

    ```text
    $ git stash push -- agent_workflows/check_engine.py && python3 -m pytest tests/test_bug_gate_check.py -o addopts=""
    ...
    >           self.assertEqual(check_engine.check_live_bug_gate(root), [])
    E           AttributeError: module 'agent_workflows.check_engine' has no attribute 'check_live_bug_gate'

    FAILED ...LiveBugGateBehaviorTests (all 6 behavioral cases)
    FAILED ...LiveBugGateEdgeTests (all 6)
    FAILED ...LiveBugGateRegistrationTests (all 3)
    FAILED ...LiveBugGateReuseTests (4 of 7)
    FAILED ...LiveBugGateSeamTests::test_full_sweep_reports_the_rule
    FAILED ...BackfillEndStateTests::test_backfilling_an_item_with_a_terminal_carrier_reaches_zero
    FAILED ...MismatchNarrowingTests::test_executed_carrier_is_skipped
    FAILED ...MismatchNarrowingTests::test_superseded_and_not_executed_carriers_are_skipped
    FAILED ...MismatchNarrowingTests::test_narrowing_uses_the_shipped_terminal_predicate
    ======================== 24 failed, 12 passed in 1.78s =========================
    ```

    THE THREE NARROWING TESTS FAILING PRE-CHANGE IS THE LOAD-BEARING PART of that result, because the OQ-03 ruling required a test that fails against today's code: `test_executed_carrier_is_skipped` and `test_superseded_and_not_executed_carriers_are_skipped` fail because pre-change code FLAGS those carriers. A narrowing whose tests passed before and after would have proven nothing. The 12 that pass pre-change are the ones asserting UNCHANGED behavior (a live carrier still flagged, matching gates clean, dangling still another rule's job, the `evaluate_blocking_close` non-use, the no-second-regex check), which is exactly the right split: the regression guards must pass on both sides.

    CONFIRMED PRESENT BY NAME, all three groups this item enumerates:
    * THE SIX BEHAVIORAL CASES, in `LiveBugGateBehaviorTests`: `test_live_gateless_bug_is_flagged`, `test_gated_bug_is_clean`, `test_done_gateless_bug_is_clean`, `test_parked_gateless_bug_is_clean`, `test_non_bug_gateless_item_is_clean`, `test_graduated_gateless_bug_with_gated_carrier_is_clean`.
    * THE REUSE ASSERTIONS (more than the two asked for, in their adapted form per V-01): `test_predicate_consumes_the_shared_carrier_index`, `test_both_consumers_use_the_one_carrier_index`, `test_the_carrier_index_is_the_only_place_the_walk_is_written`, `test_no_second_copy_of_the_blocks_release_regex`, plus `test_predicate_does_not_fork_the_live_status_vocabulary` and `test_the_live_set_agrees_with_the_creation_default`. The anti-fork assertion this plan originally specified was DROPPED as instructed and replaced by `test_evaluate_blocking_close_cannot_answer_the_open_direction`, which pins why composition is impossible rather than asserting it happened.
    * THE `check_types` SEAM TEST: `LiveBugGateSeamTests::test_full_sweep_reports_the_rule` drives `check_types(root, ["all"])` rather than the predicate, with `test_backlog_type_scope_does_NOT_report_it` and `test_whole_tree_rule_is_absent_from_the_precommit_aggregator` pinning the two seams it must NOT reach.
    * ADDITIONALLY, the cross-check the parent Set requires (both rules on ONE tree state, since satisfying the new rule is what violated the old one): `BackfillEndStateTests`, two cases.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste OQ-03's recorded answer and which option it selected FIRST; without it this item must not have run. Then paste the re-derived population with the command that produced it and state how it differs from BOTH prior readings (authored 28; review 22).
    Paste the per-item table: id6, status AS READ FROM DISK, the exact command run, and the action taken (gate applied, or exemption with reason). The `blocked` item's row must show the `--gate-kind`/`--gate-ref` flags, since review measured that the command exits 1 without them.
    Paste the FULL carrier table (review measured 15, not 11), each with its directory, and the remedy applied per OQ-03. Paste one item's `git diff` showing the expected TWO insertions (gate line plus the setter's status-history line), and confirm no hand-edit was used anywhere.
  - Observed evidence: OQ-03'S RECORDED ANSWER, FIRST, because without it this item must not have run. Answered by the maintainer on the parent (`qmgn12` OQ-03) on 2026-09-12. THE OPTION SELECTED was a REFRAMING rather than any of the four originally costed: "RESTATE `check.from-backlog-gate-mismatch` AS THE ONE-WAY OBLIGATION IT ACTUALLY MEANS, and skip a TERMINAL carrier." Its pivot question was "So any gate should be that no plan be non-blocking if it graduated from a blocking backlog item, but why would we care if a plan is blocking but the backlog is not?" The ruling explicitly DECLINED option (d) (weakening the rule to flag only a both-gated conflict), because that would drop the dropped-handoff detection the rule exists for. Applied here in the ruled ORDER: the narrowing landed FIRST (commit `5ceff69a`), then the backfill (`9e1a8d8b`), then the live-carrier co-update (`c2638561`).

    THE POPULATION, RE-DERIVED AT EXECUTION, AND IT HAS GROWN SHARPLY RATHER THAN SHRUNK. Command:

    ```text
    $ python3 -c "walk backlog._iter_items, parse with backlog.parse_item, select kind=='bug' and status in {open,blocked,graduated} and not blocks_release"
    TOTAL items: 306
    by status: {'open': 126, 'done': 93, 'graduated': 72, 'parked': 14, 'blocked': 1}
    Work-Kind bug: 178
    live bugs: 120 {'open': 71, 'graduated': 48, 'blocked': 1}
    gated: 55   GATELESS: 65   (47 open, 18 graduated, 0 blocked)
    ```

    HOW IT DIFFERS FROM BOTH PRIOR READINGS: authored **28** (16 open, 11 graduated, 1 blocked); review **22** (10 open, 11 graduated, 1 blocked); measured now **65** (47 open, 18 graduated, 0 blocked). The population has roughly TRIPLED since review six days ago, and by filename date the gateless items cluster in the last three days (26 dated 20260917, 13 dated 20260918), i.e. items filed AFTER child `di08i9`'s creation default landed. That is not the default failing (filing items during this execution produced `evidence:["blocks-release-default:next"]` each time); the route it cannot cover is RECLASSIFICATION into `bug` and hand-authoring, which is filed as backlog `98zlut`.

    THE `blocked` ITEM'S SPECIAL CASE HAS NO SUBJECT THIS RUN, stated because this item required its row. `adgtqb` is no longer in the population: it now carries a gate, so the `--gate-kind`/`--gate-ref` re-supply that review measured as mandatory was never needed. The population contains ZERO `blocked` items, so no row can show those flags. This is reported rather than silently omitted.

    THE EXACT COMMAND, identical for all 64 gated items except the status token and id6, each status READ FROM DISK and echoed back (never guessed):

    ```text
    $ python3 -m agent_workflows backlog set <status-from-disk> <id6> --blocks-release next \
        --message "Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04." \
        --yes --no-commit --agent
    === backfill complete: 64 succeeded, 0 failed, 1 skipped for judgement
    ```

    THE PER-ITEM TABLE (65 rows; status is the value read from disk before the call):

| id6    | status (from disk) | pri    | action |
|---|---|---|---|
| `cnwy8g` | graduated | medium | **EXEMPTION**, not gated (see below) |
| `nueip1` | graduated | medium | GATE APPLIED `next` |
| `cqytxf` | graduated | high | GATE APPLIED `next` |
| `13ty0u` | graduated | medium | GATE APPLIED `next` |
| `1f9m2j` | graduated | medium | GATE APPLIED `next` |
| `q0h9ls` | graduated | medium | GATE APPLIED `next` |
| `hyx1dg` | graduated | high | GATE APPLIED `next` |
| `zrzfkw` | graduated | medium | GATE APPLIED `next` |
| `5ev6lh` | graduated | medium | GATE APPLIED `next` |
| `t156g1` | graduated | high | GATE APPLIED `next` |
| `ygtykn` | graduated | medium | GATE APPLIED `next` |
| `s0303g` | graduated | medium | GATE APPLIED `next` |
| `02371s` | graduated | high | GATE APPLIED `next` |
| `46fb5i` | graduated | medium | GATE APPLIED `next` |
| `770fkp` | graduated | high | GATE APPLIED `next` |
| `894vzu` | graduated | medium | GATE APPLIED `next` |
| `fci7yn` | graduated | medium | GATE APPLIED `next` |
| `q96tpi` | graduated | medium | GATE APPLIED `next` |
| `x6tk1u` | open | high | GATE APPLIED `next` |
| `f5pttg` | open | high | GATE APPLIED `next` |
| `lb5dzj` | open | high | GATE APPLIED `next` |
| `sxlvlu` | open | medium | GATE APPLIED `next` |
| `plsx3r` | open | low | GATE APPLIED `next` |
| `tsfk8a` | open | medium | GATE APPLIED `next` |
| `cnf7gw` | open | high | GATE APPLIED `next` |
| `10pcd5` | open | medium | GATE APPLIED `next` |
| `a4em7s` | open | medium | GATE APPLIED `next` |
| `e17a2e` | open | high | GATE APPLIED `next` |
| `ipfgl1` | open | high | GATE APPLIED `next` |
| `ng4ptg` | open | medium | GATE APPLIED `next` |
| `rv2ccz` | open | medium | GATE APPLIED `next` |
| `g321ny` | open | low | GATE APPLIED `next` |
| `0zja9r` | open | medium | GATE APPLIED `next` |
| `37pfmb` | open | low | GATE APPLIED `next` |
| `3dg3dv` | open | medium | GATE APPLIED `next` |
| `5bmq5f` | open | medium | GATE APPLIED `next` |
| `8bif6g` | open | high | GATE APPLIED `next` |
| `a58s04` | open | high | GATE APPLIED `next` |
| `xw4rb7` | open | medium | GATE APPLIED `next` |
| `csmtjp` | open | medium | GATE APPLIED `next` |
| `9zyanj` | open | high | GATE APPLIED `next` |
| `vnzm27` | open | medium | GATE APPLIED `next` |
| `ifju82` | open | medium | GATE APPLIED `next` |
| `jsomff` | open | medium | GATE APPLIED `next` |
| `nmg89m` | open | medium | GATE APPLIED `next` |
| `pe7g6r` | open | high | GATE APPLIED `next` |
| `sovauj` | open | low | GATE APPLIED `next` |
| `mo3h5b` | open | high | GATE APPLIED `next` |
| `wlyg3g` | open | medium | GATE APPLIED `next` |
| `xdgorn` | open | medium | GATE APPLIED `next` |
| `xzdudk` | open | medium | GATE APPLIED `next` |
| `yyyqv7` | open | medium | GATE APPLIED `next` |
| `2oq6s8` | open | medium | GATE APPLIED `next` |
| `4vfkl1` | open | medium | GATE APPLIED `next` |
| `57dwkc` | open | medium | GATE APPLIED `next` |
| `a0s33b` | open | medium | GATE APPLIED `next` |
| `twvswo` | open | medium | GATE APPLIED `next` |
| `f5o64q` | open | low | GATE APPLIED `next` |
| `krwl3t` | open | high | GATE APPLIED `next` |
| `os1b9j` | open | medium | GATE APPLIED `next` |
| `t49rmq` | open | medium | GATE APPLIED `next` |
| `21ct62` | open | medium | GATE APPLIED `next` |
| `x7wfyx` | open | medium | GATE APPLIED `next` |
| `xtrwdb` | open | low | GATE APPLIED `next` |
| `yvp951` | open | high | GATE APPLIED `next` |

    THE ONE EXEMPTION AND ITS REASON, which is why this was not a blanket sweep. `cnwy8g` is left UNGATED. It was DE-GATED on 2026-09-09 with a recorded rationale, and its own `## Gate` section states: "No `Blocks-Release` gate. This is a layering correction, not a live failure: the ONE behavioral defect it has produced (`DriverError`) is owned by `818uru` E-03, which carries the release gate." VERIFIED AT EXECUTION rather than taken on trust: `818uru` is in `executed/` and carries `- Blocks-Release: next`, so that defect's gate was preserved and discharged. The same history entry records that the stray field was cleared precisely BECAUSE it made `aw check` report `from-backlog-gate-mismatch` against three graduated `runnerlayer` plans faithfully carrying no gate. Re-gating it would reverse a documented decision and re-create those findings. A probe confirmed my gate write would do exactly that, and was reverted. NOTE the item's authority genuinely CONFLICTS (its 2026-09-03 entry records a maintainer ruling that reclassified it to `bug` AND GATED it; the 2026-09-09 entry cleared that gate), so this is raised as DEFERRED QUESTION 04-rgaasb-Q1 rather than settled by me, and it is the single remaining `check.live-bug-ungated` finding.

    THE PRESCRIBED EXEMPTION MARKER DOES NOT WORK, which is why the exemption is recorded in this plan and the register rather than on the item. E-04 says an exempted bug "needs an explicit `- Blocks-Release: -` plus a reason in its history". Driven: an item carrying a literal `- Blocks-Release: -` trades `check.live-bug-ungated` for `check.blocks-release-dangling` (also ERROR, also I-07), so the exemption is inexpressible; and `aw backlog set <status> cnwy8g --blocks-release - --message <rationale>` on an already-ungated item returned `applied: false`, `changes: [{kind: noop}]` and wrote NOTHING, discarding the rationale (shipped bug `x6tk1u` on this path). Filed as backlog `b0dcyp`.

    THE FULL CARRIER TABLE, re-measured across ALL 65 items rather than the graduated subset. **18 carriers: 15 LIVE (`pending/`) and 3 TERMINAL (`executed/`)**, and 0 of the 18 carried a gate beforehand. Review measured 15/13/2, so the terminal set has GAINED one (`zexed1`, from item `1f9m2j`) that review did not see:

    ```text
    item 02371s (graduated) -> ld8lb3  pending    LIVE      item cnwy8g (graduated) -> 1f7xno  pending   LIVE
    item 13ty0u (graduated) -> vdabn5  pending    LIVE      item cqytxf (graduated) -> 76w6mq  pending   LIVE
    item 1f9m2j (graduated) -> zexed1  executed   TERMINAL   item f5pttg (open)      -> 4bc1nd  pending   LIVE
    item 5ev6lh (graduated) -> yeh7gc  pending    LIVE      item hyx1dg (graduated) -> h9cn0y  executed  TERMINAL
    item 770fkp (graduated) -> e4lkv5  pending    LIVE      item nueip1 (graduated) -> akzy45  pending   LIVE
    item a58s04 (open)      -> 65cuw0  pending    LIVE      item q0h9ls (graduated) -> k9awrq  pending   LIVE
    item cnwy8g (graduated) -> lyo1tz  pending    LIVE      item t156g1 (graduated) -> 5wtzqv  executed  TERMINAL
    item cnwy8g (graduated) -> 9kmbr0  pending    LIVE      item x6tk1u (open)      -> vhbvwz  pending   LIVE
                                                            item ygtykn (graduated) -> i8u6hh  pending   LIVE
                                                            item zrzfkw (graduated) -> i1hlgx  pending   LIVE
    total carriers: 18   terminal: 3   live: 15   items with a carrier: 16
    ```

    CONFIRMING THIS PLAN'S CORRECTION TO THE PARENT'S FRAMING: the affected set is NOT confined to graduated items. `f5pttg` -> `4bc1nd` and `x6tk1u` -> `vhbvwz` come from `open` items, and both carriers are in `pending/`, so the ruling covers them with no special handling. A remedy scoped to "the graduated ones" would have left two mismatches standing.

    THE REMEDY APPLIED PER OQ-03. **12 live carriers co-updated** (the 15 live, minus the 3 belonging to exempted item `cnwy8g`: `lyo1tz`, `9kmbr0`, `1f7xno`, which correctly stay ungated because their item stays ungated and so they MATCH it). Each through `aw ipd set <current-status> <path> --blocks-release next`, status read from disk: 12 succeeded, 0 failed. **The 3 TERMINAL carriers were never touched**; they stop being findings because the rule stopped over-reaching, not because they were exempted by name.

    ONE ITEM'S `git diff`, showing the expected TWO insertions (gate line plus the setter's history line):

    ```diff
    --- a/.aw/records/backlog/open/20260918-yvp951-01-yvp951-specs-set-truncates-legacy-spec-history.backlog.md
    +++ b/.aw/records/backlog/open/20260918-yvp951-01-yvp951-specs-set-truncates-legacy-spec-history.backlog.md
    @@ -1,5 +1,6 @@
      - Id: yvp951
      - Status: open
    + - Blocks-Release: next
      - Set: yvp951
      - Priority: high
      - Work-Kind: bug
    @@ -34,4 +35,5 @@
      ## Workflow history
    + - 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
      - 2026-09-18 created (aw backlog): Found by IPD diof9n (E-03): ...
    ```

    NO HAND-EDIT WAS USED ANYWHERE. Every one of the 76 record writes went through `aw backlog set` or `aw ipd set`. Proven collectively over all 64 item diffs: the ONLY added lines are 64 gate lines and 64 history lines (plus one `## Workflow history` heading the setter created for `lb5dzj`, which genuinely lacked the section), and there are ZERO removed lines:

    ```text
    $ git diff -U0 -- .aw/records/backlog | grep "^+" | grep -v "^+++" | classify
         64 [GATE LINE]        64 [HISTORY LINE]        1 +## Workflow history        1 +(blank)
    $ git diff -U0 -- .aw/records/backlog | grep "^-" | grep -v "^---" | wc -l
         0
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new rule reporting ZERO findings through the SHIPPED command identified in V-02, not through a direct predicate call. Do NOT paste `aw check backlog` clean as the proof: review measured it reporting `conforms, exit 0, findings 0` while 15 ERRORs existed, so that evidence is worthless here and offering it is a FAILED validation.
    Paste the PER-RULE `aw check all --agent` tally against the baseline captured before the first edit, and state explicitly that `check.from-backlog-gate-mismatch` is back at its baseline of ZERO. Do not claim "clean": 183 pre-existing findings are present and are not this plan's to fix, and the one live `check.from-backlog-dangling` must remain untouched.
    Paste the release-blocker count before and after (review measured 114 before and 136 after a full backfill), and a grep proving no item's `Status`, `Priority` or `Work-Kind` changed. Paste `git diff --cached --name-only` from before EACH commit proving only this item's files were staged, and re-paste it after any failed hook. State explicitly how the out-of-scope carrier edits were handled (declared in `Scope-Paths` before execution, or reconciled at finalize with a `--scope-reason` per path). Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline.
  - Observed evidence: THE NEW RULE THROUGH THE SHIPPED COMMAND IDENTIFIED IN V-02, which is `aw check all` and NOT `aw check backlog`. It reports exactly ONE `check.live-bug-ungated` finding, and that one is the deliberate `cnwy8g` exemption documented in V-04, not an unhandled violation:

    ```text
    $ PYTHONPATH=<lane> python3 -m agent_workflows check all --agent    # EXIT=1 (pre-existing findings)
    check.live-bug-ungated: 1
      .aw/records/backlog/graduated/20260903-runnerlayer-01-cnwy8g-...backlog.md
    ```

    The population went 65 -> 1, and the single survivor is the item whose de-gate is a recorded 2026-09-09 decision. So the check is at its intended floor rather than at literal zero, and the reason is stated rather than hidden. `aw check backlog` is NOT offered as evidence anywhere in this item: measured in V-02 it reports `conforms, exit 0, findings 0` on a tree that violates the rule.

    A MEASUREMENT TRAP WORTH RECORDING, because it briefly produced a WRONG answer. My first `aw check all` run reported 5 mismatches where the in-process call reported 2, which looked like the narrowing failing. Cause: the environment's `PYTHONPATH` pins `agent_workflows` to the MAIN checkout rather than the lane worktree, so the `aw` entrypoint executed main's code, not this lane's, and never saw the narrowing. Every number below is therefore taken with the lane prepended to `PYTHONPATH` and the module path verified first (`check_engine.__file__` resolving inside the lane). A lane executor who trusts a bare `aw` is measuring another tree, which is worth knowing for any runner-driven execution.

    THE PER-RULE `aw check all --agent` TALLY against the baseline captured BEFORE the first edit (both at the same tree, both with the module path pinned):

    ```text
    TOTAL findings: 447 -> 279   (exit 1 -> 1)

    rule                                                  before   after   delta
    check.from-backlog-dangling                                1       1      +0
    check.from-backlog-gate-mismatch                           2       2      +0
    check.id6-collision                                        1       1      +0
    check.ipd-uncarried-obligation                            98      98      +0
    check.lifecycle-transition-invalid                         5       5      +0
    check.live-bug-ungated                                     0       1      +1  <-- NEW RULE
    check.name-nonconformant                                   3       3      +0
    check.scope-drift                                        336     167    -169  <-- see below
    check.system-layout-missing                                1       1      +0
    ```

    `check.from-backlog-gate-mismatch` IS BACK AT ITS BASELINE. Stated exactly: its baseline is **2, NOT ZERO**, which corrects this item's own expectation. Review measured zero; at execution two findings pre-exist (`h90ij1`, `z1yefm`), and they are NOT mine: both carriers spell the gate `f33nrj` while their items spell it `next`, both spellings resolve to the SAME release record (`releases.resolve_release(repo,'next')` returns the `f33nrj` file), and neither item is in this plan's population (both are already gated). They are a false positive in a fail-closed rule, filed as backlog `0cqf33`. Leaving them is correct: reducing the count would mean editing another party's artifact, which this item forbids. THE LOAD-BEARING FACT is that the backfill created **+0** net: measured mid-run, the backfill took this rule 2 -> 14 (12 new live carriers) and the co-update took it back to 2, while the 3 terminal carriers never appeared at all because the narrowing had already landed. That is the Set's completion criterion 6 met.

    I DO NOT CLAIM "CLEAN". 279 findings remain and are not this plan's to fix. The one live `check.from-backlog-dangling` (a `From-Backlog: none` in an `executed/` plan) is UNTOUCHED at 1, exactly as required.

    THE `check.scope-drift` DROP OF 169 IS MINE BUT IS NOT THE BACKFILL, and I am attributing it rather than quietly banking it. It is caused by the `check_release_gate_consistency` narrowing's sibling effect: `is_retired` now short-circuits carriers in terminal directories. Proven by stashing ONLY my record edits and re-running, so the checker change is the sole variable:

    ```text
    with my 76 record edits STASHED (checker commit only):  check.scope-drift = 167, check.live-bug-ungated = 65
    ```

    167 with the records reverted, 167 with them applied, so the drop belongs entirely to the code change and ZERO of it to the backfill. No other party's artifact was edited to achieve it.

    THE RELEASE-BLOCKER VIEW CARRIES THE NEWLY GATED ITEMS: **109 before -> 190 after** (+81), measured through the shipped `attention.release_blockers` over `attention.scan`, the before-count taken from a detached worktree at the baseline commit `8087387e` so it is a true pre-edit reading. The +81 comprises the 64 backfilled items, the 12 co-updated carriers, and the 5 newly filed gated bug items. Gated backlog items counted directly: 105 -> 174.

    NO COLLATERAL FIELD CHANGE ON ANY ITEM. The setter takes a status positionally, so a mistake there would silently move an item's lifecycle state. Checked across the complete diff of all 64 items:

    ```text
    $ git diff -U0 -- .aw/records/backlog | grep -E "^[+-]- (Status|Priority|Work-Kind|Id|Set|Summary):" | sort | uniq -c
    (no output)
    $ git status --short -- .aw/records/backlog | grep -v "^ M" | wc -l
    0
    ```

    Not one `- Status:`, `- Priority:`, `- Work-Kind:`, `- Id:`, `- Set:` or `- Summary:` line was added or removed, and no file changed status directory. The same holds for the 12 carriers: each `aw ipd set` was passed the plan's CURRENT status, and the verified diffs show only the gate line and a history line.

    THE STAGED SET BEFORE EACH COMMIT, proving only this plan's files were staged. Four commits, each path-scoped, `git add -A` never used:

    ```text
    5ceff69a  git diff --cached --name-only ->  agent_workflows/check_engine.py
                                               tests/test_bug_gate_check.py            (2 files, both mine)
    9e1a8d8b  git diff --cached --name-only ->  64 paths, all under .aw/records/backlog/
                                               (paths NOT under that prefix: 0)
    c2638561  git diff --cached --name-only ->  12 paths, all under .aw/records/plans/pending/
                                               (the 12 live carriers; neither h90ij1 nor z1yefm present)
    0aa7c67c  git diff --cached --name-only ->  6 paths, the newly filed backlog items
    ```

    RE-VERIFIED AFTER A FAILED HOOK, as the shared-checkout rule requires. The first attempt at `5ceff69a` was REJECTED by `ruff-format` ("files were modified by this hook"). I re-ran `git diff --cached --name-only` before retrying and it still listed exactly my two files, then re-staged the reformatted versions and re-ran the new tests (36 passed) before committing. A later commit logged `[WARNING] Unstaged files detected` with pre-commit stashing and restoring; I re-checked the index immediately afterwards and found it clean. No bare `git reset` or `git stash` was used to fix an index at any point.

    HOW THE CARRIER EDITS WERE HANDLED: they are DECLARED, not reconciled after the fact. `- Scope-Paths:` already names `.aw/records/plans/pending` (added at review round 2 per OQ-03's requirement that it land "BEFORE any write"), and `agent_workflows/check_engine.py` covers the narrowing. So no `--scope-reason` is needed for any path I touched. Every changed path falls inside a declared prefix: `agent_workflows/check_engine.py`, `tests/test_bug_gate_check.py`, `.aw/records/backlog`, `.aw/records/plans/pending`. The declared-but-broad `.aw/records/plans/pending` was NOT treated as licence: exactly 12 plans were edited, each because it is a `From-Backlog` carrier the ruling requires co-updating, plus this plan itself.

    THE BARE SUITE against the pre-edit baseline, both run bare (`addopts` supplies `-q -n auto --dist=worksteal -m 'not slow'`; no `-n0`, no second `-q`, no `-p no:randomly`):

    ```text
    BEFORE (baseline, HEAD 8087387e, before the first edit):
    $ python3 -m pytest
    8100 passed, 3 skipped, 2 xfailed in 164.30s (0:02:44)

    AFTER (all work complete):
    $ python3 -m pytest
    8136 passed, 3 skipped, 2 xfailed in 99.79s (0:01:39)
    ```

    The failure SET is unchanged (empty in both), and the +36 is exactly the new `tests/test_bug_gate_check.py`. No test was broken by either the checker change or the 76-file record backfill.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: go-pending-approval`. Blocking OQ-03 was ANSWERED by the maintainer on the parent (`qmgn12`) on 2026-09-12 and is now `resolved`, so the lint gate no longer refuses it; `aw ipd lint --phase review-finalize` conforms. A human must still set it `approved` before execution.

It carries `- Item-Dependencies: executed:di08i9` because backfilling before the creation default lands would let the population re-diverge immediately, and the checker would then report violations the tooling itself was still creating.

It carries `- Blocks-Release: next` in line with the rule it enforces.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths` plus any out-of-scope path declared and reasoned at finalize with a `--scope-reason` per path (and a `--scope-ack` per declared-but-unmodified path), path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. On completion, move this file to `.aw/records/plans/executed/` with the terminal `Status:` and a workflow-history line, as the `ipd-lifecycle` post-gate step.

FIVE CORRECTIONS FROM REVIEW THAT MUST NOT BE RE-INHERITED, every one measured by executing rather than reading:

1. Do NOT quote 28, or 11 graduated plan edits. Re-measured: 22 items (10 `open`, 11 `graduated`, 1 `blocked`) and 15 carriers (13 `pending/`, 2 `executed/`), including two `open` items the plan never mentions.
2. Do NOT use `aw check backlog` as proof of anything about this rule family. It reported `conforms, exit 0, findings 0` on a tree carrying 15 of these ERRORs, because the family is wired only into the `check_types` full-sweep seam.
3. Do NOT compose the new predicate with `evaluate_blocking_close`. It returns "unchecked transition" for an ungated item and cannot express the open direction; reuse `find_from_backlog_artifacts` and the family's parse helpers instead.
4. Do NOT require any sweep to be CLEAN. Require a per-rule DELTA against a baseline captured before the first edit, and never reduce a count by editing another party's artifact.
5. Do NOT run the backfill before applying OQ-03's ruled narrowing. Executed in full WITHOUT it, the backfill produced 15 new ERROR findings, 2 against plans in `executed/` where in-place edits are forbidden. WITH the narrowing the set is 13 live carriers, and co-updating those reaches zero (both measured at review round 2).

THREE HAZARDS AT EXECUTION TIME. FIRST, this item edits at least 37 tracked files (22 items plus 15 carriers) in a SHARED CHECKOUT: verify `git diff --cached --name-only` before every commit, re-verify after any failed hook, unstage precisely with `git restore --staged <path>`, and never sweep in a change you did not make. SECOND, the backfill must not become a blanket sweep: a bug that genuinely should not gate the release needs an explicit recorded exemption, and applying `next` to all 22 without judgement would trade one silent wrongness for another. THIRD, the setter takes a status POSITIONALLY: pass each item's current status read from disk, because passing a different one transitions the artifact and appends a history line, which review reproduced on the sibling `aw ipd set` verb.
