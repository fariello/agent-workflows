# IPD: Perform the Set-wide honesty comparison across both children's shipped output

- Date: 2026-09-20
- Kind: child
- Concern: Orchestrator `ao1rb7` carries E-03, a cross-child honesty comparison of Order 01's shipped gate disclosures against Order 02's shipped contract sentences, and NO CHILD COVERS IT. Its own OQ-02 raised this at review and named "ADD AN ORDER 03 CHILD" as option (b), leaving the choice to the maintainer. On 2026-09-21 the ORCHESTRATOR COVERAGE GATE refused `aw oc run` for exactly this parent, so the question is now answered by a run that will not start. Because `retire_orchestrator` deliberately skips the `pre-transition` E/V checkpoint (`ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]`), a runner would mark `ao1rb7` `executed` with the Set's own load-bearing honesty criterion never checked.
- Scope: Perform the cross-child comparison that neither sibling can perform from inside its own fence, and correct any sentence it finds untrue. IN: read every honest-limit disclosure shipped by Order 01 (`kbqpkn`) and every commit-contract sentence shipped or left standing by Order 02 (`y9vpvv`), judge each against what the code actually does, and run the parent's three cross-IPD checks. OUT: wiring any gate (that was `kbqpkn`'s decision and it resolved to wire none), changing what any gate DECIDES, and the agent-context detector the parent defers.
- Scope-Paths: agent_workflows/hooks/, agent_workflows/engine.py, AGENTS.md, .pre-commit-config.yaml, tests/test_gate_wiring.py
- Item-Dependencies: executed:kbqpkn, executed:y9vpvv
- Status: executed
- Work-Kind: feature
- Priority: high
- Readiness: go-pending-approval
- Set: commitguard
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2s0iym
- From-Backlog: wjl471

## Workflow history
- 2026-09-23 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 2s0iym verified (set commitguard, attempt 1). [Scope reconciliation - in-scope-unmodified .pre-commit-config.yaml: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified AGENTS.md: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/engine.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/hooks/: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_gate_wiring.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-23 execution evidence recorded (opencode its_direct/pt3-claude-opus-5-1m-us): E-01..E-04 PERFORMED and V-01..V-04 recorded `pass` with pasted evidence, in run `run-20260923T024621Z-3869306` position 31, lane `aw/lane/2s0iym`, base HEAD `22cf67d9`. NO LIFECYCLE TRANSITION PERFORMED HERE: the runner owns `aw ipd begin`/`aw ipd finalize` for this run (a worker-role call is refused with `AW-LIFECYCLE-ROLE-001`), so this line records evidence only. THE SET-WIDE JUDGEMENT IS THAT NO SENTENCE SHIPPED OR PRESERVED BY `commitguard` DESCRIBES A BYPASSABLE GUARD AS AN AUTHORITY BOUNDARY, and **ZERO CORRECTIONS** were made in either half, which is the outcome the plan predicted ("Most likely shipped diff: NONE") and the parent's E-05 required. Twenty Order-01 disclosure sites enumerated and quoted (3 per opt-in gate, 2 per wired gate, plus the two `.pre-commit-config.yaml` comment blocks); the opt-in partition re-measures EXACTLY 0/0/3/3/2/2, unchanged from F-03. THE PLAN'S NAMED E-02 SUBJECT IS GONE AND THAT IS THE CORRECT VERDICT: `engine.py:1320`'s "immune to this by construction" no longer exists at this base, because Order 02 (`12ecd491`) REPLACED it with the ruled MUST wording, so it is judged SUPERSEDED and F-15's antecedent-and-mechanism method was applied to the replacement instead (DECISION 31-2s0iym-D2). The replacement's four mechanism clauses were each verified against `git_commit_helper.offer_commit` (`:579` snapshot, `:638-642` explicit-path staging, `:652` intersection, `:645`/`:695` scoped reset) and `commit_lock.commit_isolated` (`:355-361` rewrite-vs-refusal classification, one bounded retry), and the MUST is judged ACCURATE rather than an enforcement overclaim because the block ships a DECLARED ESCAPE HATCH ("If no form of `aw commit` fits your case, you MUST say so explicitly in your report"). Order 02's descriptive retry sentence DID ship; nothing was withheld. THE FOUR DRIVER-PROMPT SITES were located BY STRING as mandated, and `git commit -m msg` now measures ZERO in all four runner/generator modules while the tooled form sits at `oc_runipd.py:2178`, `agy_runipd.py:2118`, `runner_shared.py:22223` and `:22316` (every line number this Set previously cited, including the review's, is stale again). Both named cross-half contradictions were checked and are ABSENT: the retry claim is conditioned on a MUTATING hook and the two wired gates are the refusing kind, and no Order-02 sentence implies an uninstalled opt-in gate guards the commit path. `.pre-commit-config.yaml` proven byte-unchanged by `git diff bcd9755f HEAD --quiet` (`29wvmj`'s own commit), so NEITHER child modified it and `pre-push`'s absence is `kbqpkn`'s recorded decision, carried by `tests/test_gate_wiring.py:74`. `AGENTS.md` no-drift proven by the SHIPPED assertion `tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated` (10 passed), re-confirmed NON-VACUOUS this turn against a corrupted copy; the drift-blind `merge_aw_block` route was deliberately NOT used (F-07). `tests/test_gate_wiring.py` 10 passed. Bare suite BEFORE and AFTER both `3 failed, 9097 passed, 3 skipped, 2 xfailed` on the SAME three node ids, so the failing-node delta is EMPTY; note the baseline differs from F-14's review figure (`1 failed, 7942 passed`), which is why measuring locally was necessary. All three failures are pre-existing and untouchable from this fence (one environmental, `cfgj8s`; two a runner-module-layout pair). `pre-commit run --all-files`: all TEN hooks Passed including `ruff-format`, confirming F-09. THREE DECISIONS recorded and ZERO deferred questions. ONE DEFECT FOUND AND FILED: `work_cmd.py:422-423` cites a runbook directive Order 02 deleted, reported not edited (outside `Scope-Paths`), carried by backlog `t5ycse`. EXPECT FIVE `--scope-ack` FLAGS AT FINALIZE, one for EACH of the five declared `Scope-Paths` entries, because ALL FIVE are declared-but-unmodified in the realized zero-correction outcome; E-03 anticipated exactly this and a runner auto-acknowledges them (`runner_shared.py:23420` documents the derivation, `:23455` emits each `--scope-ack <path>=<note>`; the `14215-14219` citation in F-13 is STALE, one more instance of the line-number rot this Set keeps hitting). No edit was manufactured to escape the reconciliation.
- 2026-09-23 approved (aw set): Backfilled Priority and Work-Kind by inheritance from source backlog item wjl471 (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
- 2026-09-22 approved (aw set): status set to approved
- 2026-09-21 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review at HEAD cd2e6adb in an isolated lane; APPROVE WITH REVISIONS APPLIED, readiness go-pending-approval; PR-001..PR-011 all FIXED in place, none deferred, none OPEN, none REPLAN. aw ipd lint --phase author CONFORMING before review and --phase review-finalize CONFORMING after. THE PLAN'S THESIS IS SOUND AND ITS PREMISES REPRODUCE: ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint'] (ipd_lifecycle.py:2989-2999) confirms retirement skips the E/V checkpoint verbatim, the parent ALREADY carries this child (ao1rb7:63 row, :65 resolving OQ-02 to option (b)), the opt-in partition re-measures exactly 0/0 and 3/3/2/2, .pre-commit-config.yaml:17/:23 are unchanged with pre-push correctly absent, and engine.py:1320 still carries the 'immune to this by construction' sentence, so E-02 has a live subject. ELEVEN FINDINGS, ALL ABOUT WHETHER THE INSTRUCTIONS CAN BE CARRIED OUT, none disputing the shape. THE SERIOUS ONE IS THAT A VERIFICATION METHOD COULD NOT DETECT ITS OWN SUBJECT: E-04 check 3's merge_aw_block no-diff proof is drift-preserved away here, because the manifest records AGENTS.md#aw:pointer as a9deb5a1... while the live body hashes 9c9aa08f..., so _apply_section_consent takes the user-drift branch. Measured by CALLING it twice: a sentinel appended to the desired section was ABSENT from the output, and an injected HAND-EDITED string SURVIVED, both reporting action='refreshed'. A plan whose whole purpose is catching prose that overclaims a mechanism would have shipped a check that claims to prove no-drift and cannot; it now mandates tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated, verified passing (10 passed in 0.17s) AND non-vacuous against a corrupted copy. FOUR MORE WOULD HAVE MADE AN EXECUTOR FABRICATE OR MISREAD EVIDENCE: 'three sites per gate' was UNSATISFIABLE for the two wired gates because engine.py defines four create_*_gate_hook installers (:5429/:5528/:5677/:5693) and none for them, so an obedient executor would invent two rows (corrected to 3+3+3+3+2+2 plus the two config comment-block disclosures at :70-71/:75-77); the pre-authorized ruff-format failure DOES NOT EXIST (all ten hooks pass, that file is 'already formatted', and the 92-file ambient result is a version artifact of ruff 0.16.3 vs pinned rev v0.4.4), which would have licensed ignoring a real failure; ipd-executed-gate was named as a hook id when it is the entry: verb at :80 while the id is ipd-executed-transition-gate at :78, a trap tests/test_gate_wiring.py:172 documents; and ls .git/hooks FAILS outright in the lane worktree this plan runs in, so reporting it as proof of pre-push absence would conflate absent with unreadable (now reads git rev-parse --git-common-dir). MOST LIKELY TO STRAND IT IN PRACTICE: the plan's own predicted ZERO-DIFF outcome makes every declared Scope-Paths entry declared-but-unmodified, and aw ipd finalize fails closed demanding a --scope-ack each (ipd_lifecycle.py:3461-3464), whose obvious bad escape is manufacturing a cosmetic edit; E-03 now names the five acks and forbids that. ALSO FIXED: Order 02's prose surface is WIDER than assumed because y9vpvv OQ-03 was resolved to shape (a) AND extended to the four driver prompts, whose cited line numbers are stale (real: oc_runipd.py:3261, agy_runipd.py:2085, runner_shared.py:14781, :14874), so E-02 reads them by string while edit authority stays withheld; the 'immune' sentence had no judgement criterion and its antecedent is NARROW (index pollution at :1305-1319, not hook bypass), so E-02 now states the antecedent and both falsification criteria; the measured lane baseline is 1 failed, 7942 passed, 3 skipped, 2 xfailed on test_turn_bounds.py::...IS_isolation_scoped from ambient OPENCODE_CONFIG_CONTENT, NOT the test_reporting_contract.py failure both siblings cite; y9vpvv's 8baff639... hash figure is stale though its E-07 obligation stands; and the gate gained a declaration-style scope fence, the paste-actual-output hard MUST, and conditional runner-versus-executor finalize ownership. Six judgement calls recorded as D-1..D-6 in the review record, none irreversible. E-count 4 to 4; no E-item added or removed; no product code, config or sibling plan touched by this review.

- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored to own orchestrator `ao1rb7`'s E-03, which the ORCHESTRATOR COVERAGE GATE refused a run over on 2026-09-21. This plan exists because AGENTS.md prescribes adding a child for work found on a parent that no child covers, NOT deleting the parent's item: `ao1rb7`'s checklist stays exactly as it is, and this child is what makes its E-03 performable by an agent whose work passes the pre-transition E/V checkpoint. THE PARENT ALREADY ARGUED FOR THIS PLAN: its OQ-02 states option (b) verbatim ("ADD AN ORDER 03 CHILD that performs the cross-child read after both land, which AGENTS.md prescribes"), calls option (b) "more robust", and defers only because the choice depended on whether a runner would be used. A runner was used and refused, so option (b) is selected. MEASURED AT HEAD `41f6a45b` BEFORE AUTHORING, and two of the parent's stated premises are now STALE IN THE PLAN'S FAVOR. FIRST, `kbqpkn` is `executed` and it WIRED NOTHING: its OQ-01 resolved all four gates to "leave opt-in", so the comparison this plan performs is mostly a preservation check rather than a correction sweep, and the cheap outcome the parent's E-05 predicted ("every disclosure is unchanged and still true") is the likely one. Verified the partition the parent relies on still holds exactly: `grep -ci opt-in` over `agent_workflows/hooks/` gives 0 for both WIRED gates (`executed_transition_gate.py`, `status_untooled_gate.py`) and 3, 2, 3, 2 for the four opt-in ones (`ipd_dependency_statement_gate.py` 3, `precommit_scope_gate.py` 3, `backlog_blocking_close_gate.py` 2, `prepush_authorization_gate.py` 2). Also verified `.pre-commit-config.yaml` still registers only `ipd-executed-gate` (line 80) and `ipd-status-untooled-gate` (line 93), `default_install_hook_types: [pre-commit, pre-merge-commit]` (line 17) and `default_stages: [pre-commit]` (line 23) are unchanged, and the only installed hook in `.git/hooks` is still `pre-commit`, so `kbqpkn` genuinely added no stage. SECOND, THE PARENT'S E-02 BLOCKER HAS CLEARED: the parent says twice to "expect this edge to hold rather than to pass" because `lqly9m` was `to-review`, but `lqly9m` is now `- Status: executed` in `.aw/records/plans/executed/20260908-hookretry-01-lqly9m-...`, so `y9vpvv`'s `Item-Dependencies: executed:lqly9m` is SATISFIED and Order 02 can run. That is why this plan declares `executed:y9vpvv` as a real edge rather than as an aspiration. THE `immune to this by construction` SENTENCE THE SET IS ABOUT IS STILL LIVE at `engine.py:1320`, so Order 02's work is genuinely outstanding and this comparison has something to compare.
- 2026-09-20 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Perform the one check in the `commitguard` Set that spans both children, so the Set's completion criterion "no sentence shipped by either child describes a bypassable guard as an authority boundary" is verified by something that a pre-transition E/V checkpoint actually gates, rather than parked on a parent a runner retires without reading.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: read both halves and judge every sentence

- [x] E-01 ENUMERATE AND QUOTE EVERY HONEST-LIMIT DISCLOSURE SHIPPED OR PRESERVED BY ORDER 01, then judge each against what the gate actually does. Order 01 wired nothing, so its deliverable was `tests/test_gate_wiring.py` plus the finding that all four gates stay opt-in; the disclosures it PRESERVED are therefore the subject. Quote each sentence with its `file:line`, and for each state whether it accurately describes a bypassable local check.
  THE SITES ARE THREE PER GATE, not one, and the parent's E-05 measured this: a gate's claim lives in (a) its module docstring, (b) its PRINTED refusal text, and (c) its `engine.create_*_hook` installer docstring. Do NOT grep for `opt-in` alone and call the enumeration done: a sentence can overclaim without using that phrase, which is exactly the failure mode (`"NOT an authority boundary"` is the honest form, and its absence is what matters).
  BUT SITE (c) DOES NOT EXIST FOR THE TWO WIRED GATES, so the "three per gate for all six" instruction was UNSATISFIABLE AS WRITTEN and is corrected here. MEASURED AT REVIEW: `engine.py` defines exactly FOUR installers, `create_backlog_close_gate_hook` (`engine.py:5429`), `create_dependency_gate_hook` (`:5528`), `create_precommit_scope_gate_hook` (`:5677`) and `create_prepush_authorization_gate_hook` (`:5693`), one for each OPT-IN gate. There is NO `create_*` installer naming `executed_transition_gate` or `status_untooled_gate`, and that absence is CORRECT BY DESIGN: those two are wired in `.pre-commit-config.yaml` and need no opt-in installer. So the site count is THREE for each of the four opt-in gates and TWO for each of the two wired ones. Do NOT fabricate a third row for a wired gate.
  THE WIRED GATES' THIRD DISCLOSURE SURFACE IS THE CONFIG COMMENT BLOCK, and it must be read, because it is where a wired gate's honest limit actually lives. Read `.pre-commit-config.yaml:70-71` ("Best-effort/local only (skippable with --no-verify) ... No CI enforcement.") and `:75-77` (the `pre-merge-commit` honest limit naming the fast-forward and conflicted-then-resolved paths). Those sentences are part of this Set's shipped prose surface and E-03's Set-wide claim is not Set-wide without them.
  ALSO IGNORE `agent_workflows/hooks/__init__.py`, which is not a gate module and measures 0. There are SIX gate modules, not seven.
  THE EXPECTED VERDICT IS "ALL ACCURATE, UNCHANGED", AND THAT IS A COMPLETE OUTCOME. Because `kbqpkn` wired nothing, every "OPT-IN" string remains true, and the parent's E-05 is explicit: "DO NOT 'FIX' THE DISCLOSURES IF YOU WIRE NOTHING ... editing them would create the very drift this item guards against." So a finding of zero corrections is the likely correct result and must be recorded as such, not padded with edits.
  - Depends on: none
  - Expected outcome: a table with one row per disclosure site: THREE for each of the four opt-in gates (module docstring, printed refusal text, `engine.create_*_hook` docstring) and TWO for each of the two wired gates (module docstring, printed refusal text), plus the two `.pre-commit-config.yaml` comment-block disclosures. Each row carries the quoted sentence, its `file:line`, and an accurate/inaccurate verdict; plus an explicit count of corrections made, which may legitimately be zero.
  - Execution state: performed

- [x] E-02 ENUMERATE AND QUOTE EVERY COMMIT-CONTRACT SENTENCE SHIPPED BY ORDER 02, then judge each the same way. Order 02 (`y9vpvv`) lands the ruled MUST wording plus `aw commit --no-plan`, and it rewrites the managed block installed into EVERY managed repo, so an overclaim here propagates further than a gate docstring.
  THE SPECIFIC SENTENCE THIS SET EXISTS TO GET RIGHT is at `engine.py:1320` and reads "PREFER THE TOOLED COMMIT PATH, which is immune to this by construction". Verified present at HEAD `41f6a45b` and re-verified at review (still `engine.py:1320`). "Immune by construction" is precisely the class of claim the Set forbids if a `--no-verify` or a hand-staged index can defeat it, so judge it against the code rather than against its own confidence, and check whether Order 02 replaced, narrowed, or left it.
  JUDGE "IMMUNE TO THIS" AGAINST ITS ANTECEDENT, WHICH IS NARROW, because the obvious reading is the wrong one and would manufacture a false finding. "THIS" refers to the preceding paragraph's hazard, namely a POLLUTED INDEX sweeping a co-worker's staged edit into your commit (`engine.py:1305-1319`), NOT to hook bypass in general. So the sentence claims only that `offer_commit` cannot commit a path you did not name, and its own next clause states the mechanism: it "snapshots the index BEFORE staging, stages only your explicit paths, commits only the intersection of those paths with what it itself staged". VERIFY THAT MECHANISM against `git_commit_helper.offer_commit` (`git_commit_helper.py:407`), whose docstring says "ONLY these are ever staged". If the intersection behavior holds, the sentence is TRUE AS SCOPED and the correct verdict is ACCURATE, with the antecedent stated.
  WHAT WOULD MAKE IT FALSE, so the check is real and not a rubber stamp: a demonstration that the tooled path can commit a path the caller did not name, or wording that generalizes "immune" beyond the index-pollution hazard (for example to `--no-verify`, to hook enforcement, or to authority over what lands). THE HONEST LIMIT TO CHECK FOR ABSENCE OF is that `aw commit` is a CONVENIENCE WRAPPER, not an authority boundary: nothing prevents an agent from running raw `git` instead. If Order 02's rewrite upgrades PREFER to MUST, re-judge under the stronger claim, because a MUST invites the reading that the tooled path is enforced when it is not.
  CHECK THE RENDERED COPY TOO, NOT ONLY THE SOURCE. `AGENTS.md` is GENERATED from `engine.py`, so a corrected sentence in the generator that was never regenerated leaves the false sentence in the file agents actually read. Compare both.
  IF ORDER 02's RETRY SENTENCE WAS WITHHELD, SAY SO AND WHY. Order 02's E-05 permits shipping the imperative while withholding the descriptive retry sentence if the retry is absent. `lqly9m` is now `executed`, so the retry SHOULD exist and the full wording should have shipped; if it did not, that is a finding, because a withheld sentence with a satisfied dependency means something else went wrong.
  THE FOUR DRIVER-PROMPT SITES ARE PART OF ORDER 02's SHIPPED PROSE AND ARE IN THIS ITEM'S SUBJECT, which the plan previously missed. `y9vpvv`'s OQ-03 was RESOLVED by the maintainer on 2026-09-10 to shape (a) AND explicitly extended the mandate: "the four driver prompts ... get the same treatment, because that is where a runner-executed agent actually reads its instructions." So Order 02 ships prose OUTSIDE `engine.py` and `AGENTS.md`, and a comparison that reads only those two files is not reading Order 02's whole half. MEASURED AT REVIEW, the raw-`git commit` instruction currently lives at `oc_runipd.py:3261`, `agy_runipd.py:2085` and `runner_shared.py:14781` and `:14874`; the `:2607`/`:4963`/`:1794`/`:2506` line numbers `y9vpvv` cites are STALE, so LOCATE THE SITES BY STRING (`git commit -m msg -- <path>` and `git commit -m msg -- <paths>`) rather than by line number.
  THOSE FILES ARE NOT IN THIS PLAN'S `Scope-Paths`, DELIBERATELY: this item READS them to judge, and reading is not declaring. If a driver-prompt sentence is found untrue, that is a FINDING TO REPORT, not an edit to make here; E-03's corrective-IPD branch is the route.
  - Depends on: none
  - Expected outcome: every contract sentence Order 02 shipped or left standing is quoted with its `file:line` and judged, INCLUDING the four driver-prompt sites located by string; the `engine.py:1320` claim is explicitly addressed; source and rendered `AGENTS.md` agree; and the retry sentence's presence or absence is stated with its reason.
  - Execution state: performed

### Task group 2: the cross-child comparison and the parent's cross-IPD checks

- [x] E-03 COMPARE THE TWO HALVES AGAINST EACH OTHER, which is the work no sibling can do and the entire reason this plan exists. E-01 and E-02 each read ONE half; this item asks the question that spans them: does anything Order 01 shipped or preserved contradict anything Order 02 shipped?
  THE CONCRETE CONTRADICTION TO LOOK FOR, which the parent's cross-IPD section names: Order 01's half makes gates fire (or documents why they deliberately do not), while Order 02's wording tells agents the tooled path costs no round trip. If a gate REFUSES rather than rewrites, the retry claim does not cover it, and wording implying otherwise is the failure. Because Order 01 wired nothing, ALSO check the inverse asymmetry this creates: Order 02's wording must not imply a gate protects the commit path when that gate is opt-in and not installed here.
  STATE THE RESULT AS A CLAIM ABOUT THE SET, not as a per-file pass. The Set's completion criterion is a property of the whole shipped output, so the evidence must be a judgement over both halves together, naming any sentence corrected and in WHICH child's owning file.
  WHERE A CORRECTION BELONGS. The parent's scope check is explicit that a fix goes in the OWNING child's fence, but both siblings will be terminal when this runs, and AGENTS.md forbids adding commits to an executed plan. So this plan declares both halves' paths in its own `Scope-Paths` and makes the correction HERE, naming which child's territory it touched and why the correction could not be made there. If a correction turns out to be large enough to need its own review, file a corrective IPD instead and record that decision.
  THE EXPECTED ZERO-EDIT OUTCOME HAS A FINALIZE CONSEQUENCE YOU MUST PLAN FOR, and it is the single most likely way this plan gets stuck. Because the most likely result is NO DIFF AT ALL, every one of the five declared `Scope-Paths` will be DECLARED-BUT-UNMODIFIED, and `aw ipd finalize` FAILS CLOSED on exactly that: `_reconcile_scope` requires an acknowledgment per untouched declared path and refuses headless with "declared-but-unmodified path needs a --scope-ack: <p>" (`ipd_lifecycle.py:3461-3464`, computed at `:2108-2112`). So finalize with an explicit ack for each path that this execution did not change, for example `--scope-ack agent_workflows/hooks/=read-only-judgement --scope-ack agent_workflows/engine.py=read-only-judgement --scope-ack AGENTS.md=read-only-judgement --scope-ack .pre-commit-config.yaml=read-only-judgement --scope-ack tests/test_gate_wiring.py=read-only-judgement`, dropping any path you genuinely did change. THIS IS NOT A DEFECT AND MUST NOT BE "FIXED" BY MANUFACTURING AN EDIT to make a path look touched: the acks are the honest record that this is a read-and-judge plan. Note a RUNNER auto-acknowledges these (`runner_shared.py:14215-14219`), so this matters most when a human or agent finalizes by hand.
  - Depends on: E-01, E-02
  - Expected outcome: an explicit statement that no sentence shipped by this Set describes a bypassable guard as an authority boundary, or the offending sentences QUOTED and corrected with the owning child named; plus a statement of whether any correction was made here versus deferred to a corrective IPD.
  - Execution state: performed

- [x] E-04 RUN THE PARENT'S THREE CROSS-IPD CHECKS, which are part of its E-03 scope and which a retiring runner also skips. These are mechanical and independent of the sentence judgement, so they are separated from E-03 rather than bundled into it.
  CHECK 1, `.pre-commit-config.yaml` INTEGRITY: confirm `default_install_hook_types` contents, and confirm `29wvmj`'s `pre-merge-commit` key plus its explanatory comment block are BYTE-UNCHANGED. MEASURED AT HEAD `41f6a45b`: the file has `default_install_hook_types: [pre-commit, pre-merge-commit]` (line 17) and `default_stages: [pre-commit]` (line 23), and `pre-push` is ABSENT because `kbqpkn` wired nothing. So the parent's expectation that this list would contain three entries is STALE; the correct check is that the two original entries survived and that the absence of `pre-push` matches `kbqpkn`'s recorded decision rather than an omission.
  READ THE INSTALLED-HOOK FACT FROM THE GIT COMMON DIR, NOT FROM `.git/hooks`. This plan will execute in an ISOLATED LANE WORKTREE, where `.git` is a FILE pointing at the worktree's gitdir and `ls .git/hooks` fails with "Not a directory" (measured in this review). The installed-hook set is SHARED and lives at `"$(git rev-parse --git-common-dir)/hooks"`, which measures a single `pre-commit`. Use that form, and do not report the `.git/hooks` failure as evidence that no hook is installed: those are different claims and conflating them would make the `pre-push` absence look proven when it was merely unreadable.
  CHECK 2, WIRING-VERSUS-WORDING NON-CONTRADICTION: this is E-03's subject, so here just confirm the mechanical input to it, namely which gates are registered and which are not. MEASURED AT REVIEW, with the ids corrected because the plan previously named one of them wrongly: the registered hook IDS are `ipd-executed-transition-gate` (`.pre-commit-config.yaml:78`) and `ipd-status-untooled-gate` (`:93`). `ipd-executed-gate` is NOT an id, it is the VERB that first hook's `entry:` invokes (`:80`), and `tests/test_gate_wiring.py:172` records exactly this trap ("id is free text ... while the verb is what must match"). The four opt-in gates appear ZERO times. Cite the id when you mean the registration and the verb when you mean the entry point.
  CHECK 3, `AGENTS.md` REGENERATES WITH NO DIFF, AND THE OBVIOUS METHOD FOR IT IS BROKEN. Do NOT prove this by calling `merge_aw_block` and diffing its output against the file: that route CANNOT DETECT A HAND EDIT in this repository today, so a passing result would be meaningless. MEASURED AT REVIEW: `.aw/system/managed-sections.json` records `AGENTS.md#aw:pointer` as `a9deb5a1d76e603e6c016d5ea0c2f676010bd4910297ffa16aa5b52647897fc4` while the live section body hashes `9c9aa08f3f67f8e637d16d58951c8e243ac1c66c928820ef357c7068c7eefe87`, so `matches_recorded` returns FALSE and `_apply_section_consent` (`engine.py:1792`) takes the user-drift branch and PRESERVES THE ON-DISK BODY. Proven twice by calling it: appending a sentinel to the desired `pointer` section returned `action='refreshed'` with the sentinel ABSENT from the output; and injecting a literal `HAND-EDITED` string into the on-disk copy returned `action='refreshed'` with THE HAND EDIT STILL PRESENT. Note the live hash is `9c9aa08f...`, NOT the `8baff639...` that `y9vpvv`'s E-07 and its review both record, so that figure is STALE TOO and must not be copied.
  USE THE SHIPPED ASSERTION INSTEAD, which compares the file's block against `engine.agents_managed_block(target_layout="aw")` directly and bypasses the consent layer entirely: run `python3 -m pytest tests/test_shared_checkout_contract.py` and cite `NoDriftTests::test_repo_agents_block_equals_generated`. VERIFIED AT REVIEW that it both passes today (`10 passed in 0.17s`) and is NON-VACUOUS: the same comparison performed against a copy carrying an injected `HAND-EDITED` string returns unequal, so it genuinely detects the drift the consent path hides. Paste that summary line as the no-diff proof.
  DO NOT "FIX" THE STALE MANIFEST HASH HERE. Reconciling it is `y9vpvv`'s E-07, which owns that work and must run before its own regeneration; writing `.aw/system/managed-sections.json` from this plan would both duplicate a sibling's item and touch a path this plan does not declare.
  ALSO CONFIRM `tests/test_gate_wiring.py` STILL PASSES AND IS STILL NON-VACUOUS, since it is `kbqpkn`'s only shipped deliverable and it is the durable guard against a seventh gate being added unclassified. Run it and paste the summary line.
  - Depends on: E-03
  - Expected outcome: all three cross-IPD checks performed with pasted evidence; the `pre-push` absence explained against `kbqpkn`'s decision rather than reported as a defect; `AGENTS.md` regeneration showing no diff; `tests/test_gate_wiring.py` passing.
  - Execution state: performed

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, AND A PARENT'S UNCOVERED ITEM GETS A CHILD RATHER THAN A DELETION. AGENTS.md: "if you are authoring a Set and find yourself writing a STEP on the Order-0 plan that no child covers, do NOT delete it: ADD A CHILD for it." This plan IS that child. `ao1rb7`'s checklist is left exactly as authored.
- `retire_orchestrator` SKIPS THE PRE-TRANSITION E/V CHECKPOINT BY DESIGN, recorded in `ipd_lifecycle.ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]` on the premise that "an orchestrator's items are performed by NOBODY". That premise is what makes parked parent work dangerous, and it is the mechanism the coverage gate now checks before spending a turn.
- `kbqpkn` WIRED NOTHING, AND THAT WAS THE CORRECT OUTCOME. Its OQ-01 found all four gates deliberately opt-in by a resolved maintainer decision in executed plan `diundn` ("NEVER installed by default"), and two of the four additionally FAIL a safety check (`precommit-scope-gate` refuses a clean tree with `check.scope-drift` findings against other agents' in-flight plans; `prepush-authorization-gate` exits 1 by design without `AW_PUSH_AUTHORIZED=1`). Its shipped deliverable is `tests/test_gate_wiring.py`, which pins the wired/exempt partition so a NEW gate cannot be added unclassified.
- THE OPT-IN PARTITION IS MECHANICAL AND CURRENT. `grep -ci opt-in` over `agent_workflows/hooks/`: `executed_transition_gate.py` 0, `status_untooled_gate.py` 0, `ipd_dependency_statement_gate.py` 3, `precommit_scope_gate.py` 3, `backlog_blocking_close_gate.py` 2, `prepush_authorization_gate.py` 2. Re-measured at HEAD `41f6a45b`.
- `AGENTS.md` IS GENERATED FROM `engine.py`, so any prose correction must be made in the generator and regenerated, never hand-edited in the rendered file.
- A DISCLOSURE LIVES IN THREE PLACES PER OPT-IN GATE: module docstring, printed refusal text, and `engine.create_*_hook` installer docstring. A one-site fix leaves two false copies. CORRECTED AT REVIEW: a WIRED gate has only the first two, because it has no opt-in installer (`engine.py` defines four `create_*_gate_hook` functions, one per opt-in gate, and none for `executed_transition_gate` or `status_untooled_gate`). A wired gate's third disclosure surface is the `.pre-commit-config.yaml` comment block instead (`:70-71`, `:75-77`).
- THE REGENERATION CONSENT LAYER HIDES DRIFT IN THIS REPOSITORY TODAY, so a `merge_aw_block` round-trip is NOT a valid no-drift proof: `_apply_section_consent` preserves the on-disk `pointer` body because the manifest's recorded hash disagrees with disk. The valid proof is `tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated`, which compares against `engine.agents_managed_block(target_layout="aw")` directly and was verified non-vacuous at review.
- A HOOK ID AND A GATE VERB ARE DIFFERENT STRINGS, and `tests/test_gate_wiring.py:172` says so explicitly. Cite the id for a registration and the verb for an entry point.
- IN A LANE WORKTREE `.git` IS A FILE, so installed hooks must be read from `git rev-parse --git-common-dir`.

## Findings

| Id | Severity | Location (measured at HEAD `41f6a45b`) | Finding | Evidence |
|---|---|---|---|---|
| F-01 | info | `ao1rb7` OQ-02 | The parent itself proposed this plan as option (b) and called it "more robust", deferring only on whether a runner would be used. A runner was used and refused, so the deferral condition resolved. | Parent OQ-02 text: "ADD AN ORDER 03 CHILD that performs the cross-child read after both land". |
| F-02 | error | `ao1rb7` E-03 + `ipd_lifecycle.ROLLUP_OMITTED_GATES` | The parent's E-03 is covered by no child, and orchestrator retirement skips the E/V checkpoint, so a runner would report it complete unperformed. This is the defect this plan closes. | `ORCHESTRATOR COVERAGE GATE` refused `aw oc run` naming `ao1rb7` on 2026-09-21. |
| F-03 | info | `agent_workflows/hooks/` | The wired-versus-opt-in partition the parent relies on still holds exactly: 0/0 for the two wired gates, 3/2/3/2 for the four opt-in ones. | `grep -ci opt-in` per module, re-measured. |
| F-04 | warn | `ao1rb7` E-02 and its gate prose | The parent says twice to expect Order 02 to defer as `dependency-blocked` because `lqly9m` was `to-review`. STALE: `lqly9m` is now `executed`, so the edge is satisfied and Order 02 can run. Do not read the parent's prose as current. | `.aw/records/plans/executed/20260908-hookretry-01-lqly9m-...ipd.md` reads `- Status: executed`. |
| F-05 | warn | `ao1rb7` cross-IPD check 1 | The parent expects `default_install_hook_types` to contain `pre-push` after the Set. STALE: `kbqpkn` wired nothing, so the list is still `[pre-commit, pre-merge-commit]` and `pre-push` is correctly absent. E-04 checks preservation, not addition. | `.pre-commit-config.yaml:17`; only `pre-commit` in `.git/hooks`. |
| F-06 | info | `engine.py:1320` | The "immune to this by construction" claim the Set exists to judge is still live at HEAD, so E-02 has a real subject. | `grep -n "immune to this by construction" agent_workflows/engine.py` -> line 1320. |
| F-07 | error | `.aw/system/managed-sections.json` + `engine.py:1792` | **E-04's ORIGINAL CHECK-3 METHOD COULD NOT DETECT WHAT IT CLAIMED TO.** A `merge_aw_block` no-diff proof is drift-preserved away today: the manifest records `AGENTS.md#aw:pointer` as `a9deb5a1...` while the live body hashes `9c9aa08f...`, so `_apply_section_consent` preserves disk. Proven by injecting `HAND-EDITED` into the on-disk copy: `action='refreshed'` and THE HAND EDIT SURVIVED. Check 3 now mandates the shipped assertion instead. | Measured at review by calling `merge_aw_block` twice (sentinel absent; hand edit preserved). |
| F-08 | error | plan E-01 | **THE "THREE SITES PER GATE FOR ALL SIX GATES" INSTRUCTION WAS UNSATISFIABLE.** Site (c), the `engine.create_*_hook` installer docstring, exists ONLY for the four opt-in gates; `engine.py` defines exactly four installers (`:5429`, `:5528`, `:5677`, `:5693`) and NONE for the two wired gates. An executor obeying the text literally would have fabricated two rows. Corrected to 3+3+3+3+2+2 plus the two config comment blocks. | `grep -n "^def create_.*gate_hook" agent_workflows/engine.py` -> four results, none for the wired gates. |
| F-09 | error | plan "Required tests / validation" | **THE PRE-AUTHORIZED `ruff-format` FAILURE DOES NOT EXIST.** `pre-commit run --all-files` passes ALL TEN hooks at review, and `tests/test_cli_output_docs_rollout.py` reports "1 file already formatted". Pre-authorizing an absent failure would have licensed ignoring a real one the executor introduced. The 92-file ambient `ruff format --check` result is a VERSION ARTIFACT (ambient 0.16.3 vs pinned `rev: v0.4.4`). | `pre-commit run --all-files` -> ten `Passed`; `.pre-commit-config.yaml:43`. |
| F-10 | warn | plan E-02 | **ORDER 02's PROSE SURFACE IS WIDER THAN THE PLAN ASSUMED.** `y9vpvv` OQ-03 was resolved to shape (a) AND extended to the four driver prompts, so Order 02 ships prose outside `engine.py`/`AGENTS.md`. E-02 now reads them. Their cited line numbers are STALE: the instruction lives at `oc_runipd.py:3261`, `agy_runipd.py:2085`, `runner_shared.py:14781` and `:14874`, so locate by string. | `y9vpvv:196`; `grep -n "git commit -m msg --" agent_workflows/*.py`. |
| F-11 | warn | plan E-04 | **`ipd-executed-gate` IS A VERB, NOT A HOOK ID.** The registered ids are `ipd-executed-transition-gate` (`.pre-commit-config.yaml:78`) and `ipd-status-untooled-gate` (`:93`); `ipd-executed-gate` is the `entry:` verb at `:80`. `tests/test_gate_wiring.py:172` records this exact trap. Check 2 now distinguishes them. | `grep -n "^      - id:" .pre-commit-config.yaml`. |
| F-12 | warn | plan E-04 | **`ls .git/hooks` FAILS IN A LANE WORKTREE** ("Not a directory": `.git` is a file). The shared installed-hook set is at `"$(git rev-parse --git-common-dir)/hooks"`, measuring one `pre-commit`. Reporting the failure as proof that no `pre-push` is installed would conflate "absent" with "unreadable". | Measured in this lane: `ls .git/hooks` -> exit 2; common-dir form -> `pre-commit`. |
| F-13 | warn | plan E-03 / finalize | **THE EXPECTED ZERO-EDIT OUTCOME WOULD REFUSE AT FINALIZE.** With no diff, all five declared `Scope-Paths` are declared-but-unmodified, and `_reconcile_scope` fails closed demanding a `--scope-ack` each (`ipd_lifecycle.py:3461-3464`). E-03 now names the acks, so the executor does not manufacture an edit to escape the refusal. | `ipd_lifecycle.py:2108-2112`, `:3461-3464`; `runner_shared.py:14215-14219`. |
| F-14 | warn | plan "Required tests / validation" | **THE LANE'S ACTUAL SUITE FAILURE IS A DIFFERENT ONE.** Measured here: `1 failed, 7942 passed, 3 skipped, 2 xfailed`, failing `tests/test_turn_bounds.py::...test_the_permission_policy_by_contrast_IS_isolation_scoped` because `OPENCODE_CONFIG_CONTENT` is in the agent session's ambient env (`tests/test_turn_bounds.py:310`). The `test_reporting_contract.py` failure both siblings cite did NOT reproduce. | Bare `python3 -m pytest`; reproduced standalone. |
| F-15 | info | plan E-02 | The `engine.py:1320` claim's antecedent is NARROW (index pollution, `engine.py:1305-1319`), not hook bypass, so the likely correct verdict is ACCURATE-AS-SCOPED. E-02 now states the antecedent and the falsification criterion, so the judgement cannot be a rubber stamp in either direction. | `engine.py:1320-1324`; `git_commit_helper.py:407` ("ONLY these are ever staged"). |
| F-16 | info | `y9vpvv` E-07 | The `8baff639...` live-hash figure `y9vpvv` and its review both record is STALE; the pointer section now hashes `9c9aa08f...`. The DRIFT still exists, so `y9vpvv`'s E-07 remains necessary, but its cited number must not be copied. | `manifest_mod.hash_content` over the parsed pointer body. |

## Proposed changes (ordered, validatable)

1. Enumerate and quote every Order 01 disclosure site across all three site classes, judging each against actual behavior (E-01).
2. Enumerate and quote every Order 02 contract sentence, including the `engine.py:1320` claim, in both generator and rendered form (E-02).
3. Compare the two halves against each other and correct any sentence that describes a bypassable guard as a boundary, naming the owning child (E-03).
4. Run the parent's three cross-IPD checks plus `tests/test_gate_wiring.py`, with the `pre-push` absence explained against `kbqpkn`'s decision (E-04).

Most likely shipped diff: NONE, with a recorded judgement that every sentence is accurate. That is a complete and correct outcome, and the plan must not manufacture an edit to look productive.

## Deferred / out of scope (with reason)

- WIRING ANY GATE. `kbqpkn` resolved all four to "leave opt-in" on a cited maintainer decision, and two additionally fail a safety check. Reversing that is not this plan's business.
  - Carrier-Declined: A RESOLVED MAINTAINER DECISION, not an outstanding obligation. Executed plan `kbqpkn`'s OQ-01 settled all four gates as deliberately opt-in, citing `diundn`'s "NEVER installed by default" ruling. There is no future state in which this Set should wire them, so a carrier would assert pending work that nobody owes.
- CHANGING WHAT ANY GATE DECIDES. The parent's E-03-versus-E-05 boundary applies here verbatim: a disclosure STRING may be corrected, a predicate may not. A `git diff` on any touched hook module must show only docstring and literal-text lines.
  - Carrier-Declined: A SCOPE BOUNDARY, not deferred work. Correcting a false disclosure string and changing a predicate are different acts, and this plan does only the former. Nothing is left undone for a carrier to hold.
- THE AGENT-CONTEXT DETECTOR AND THE NEW COMMIT GUARD (backlog `wjl471` FINDING 1, its OQ-1..OQ-4). The parent defers these explicitly and they need a maintainer ruling on shape.
  - Carrier-Declined: Already carried by an OPEN backlog item: `wjl471` remains open and holds FINDING 1 plus its four open questions. Naming a second carrier here would duplicate a live record.
- CLOSING BACKLOG `wjl471`. The parent's OQ-01 is open on whether the item survives this Set, and it recommends keeping it open for the guard design. This plan does not close it.
  - Carrier-Declined: The item itself is the record, and it stays OPEN by the parent's own OQ-01 recommendation. An obligation to keep something open needs no carrier; closing it prematurely is the risk, and that is the parent's question to settle.
- FIXING `check.scope-drift`'s STALE-FROZEN-BASE DEFECT, which is why `precommit-scope-gate` refuses a clean tree. Plan `wmnmei` (Set `rcptstale`) owns it.
  - Carrier-Declined: Already carried by plan `wmnmei` (Set `rcptstale`), which owns this defect. A second carrier would duplicate it.
- THE `Readiness:` FIELD. Written by `/plan-review` on 2026-09-21, which is the only legitimate author of it. It was correctly ABSENT while this plan was unreviewed.
  - Carrier-Declined: Now an ATTESTED REVIEW OUTPUT rather than an omission. Nothing is left for a carrier.
- RECONCILING THE STALE `AGENTS.md#aw:pointer` MANIFEST HASH. `y9vpvv`'s E-07 owns it and must run it before its own regeneration; this plan neither declares `.aw/system/managed-sections.json` nor duplicates a sibling's item.
  - Carrier-Declined: Already carried by `y9vpvv` E-07, which is `approved` and explicitly names this as a prerequisite of its own E-04. A second carrier would duplicate it. Note only the plan's CITED HASH is stale (F-16); the drift itself is live, so the item is still owed.
- CORRECTING A DRIVER-PROMPT SENTENCE. E-02 READS the four driver-prompt sites to judge Order 02's half, but `oc_runipd.py`, `agy_runipd.py` and `runner_shared.py` are deliberately NOT declared in `Scope-Paths`: reading is not declaring. A sentence found untrue there is REPORTED, and E-03's corrective-IPD branch is the route.
  - Carrier-Declined: A SCOPE BOUNDARY between judging and editing, not deferred work. The judgement itself IS performed here (E-02), so nothing is left undone; only the edit authority is withheld, and E-03 already names where an edit would go.
- FIXING `tests/test_turn_bounds.py`'s AMBIENT-ENVIRONMENT FAILURE (F-14). It fails because `OPENCODE_CONFIG_CONTENT` is set in the executing agent's session, which is an environment fact and not a repository defect this plan's fence can reach.
  - Carrier-Declined: NOT A DEFECT IN THIS PLAN'S SUBJECT and not plausibly caused by it. Recording it as the measured baseline (which the validation section now does) is the correct treatment; asserting a carrier would invent an obligation nobody owes. If it proves to be a genuine test-isolation bug, it belongs to a new backlog item raised on its own evidence, not to this Set.

## Scope check

- Over-scope: none. This plan reads and judges prose that the Set already shipped, and corrects only a sentence found untrue.
- Scope-Paths justification: the declared paths are the UNION of both children's prose surfaces, because a cross-child comparison must be able to correct either half and both siblings will be terminal when this runs (AGENTS.md forbids adding commits to an executed plan). `agent_workflows/hooks/` and `.pre-commit-config.yaml` are Order 01's territory, `agent_workflows/engine.py` and `AGENTS.md` are Order 02's, and `tests/test_gate_wiring.py` is read to confirm it still passes. Declaring them is NOT a licence to re-decide either child's work: E-03 states the narrow rule (correct a false disclosure string, never a predicate).
- Under-scope: this plan wires no gate, writes no new guard, changes no gate's decision logic, closes no backlog item, and fixes no scope-drift defect. Each is excluded above with its reason.

## Required tests / validation

- `tests/test_gate_wiring.py` passes, and its non-vacuity is confirmed rather than assumed (the file is `kbqpkn`'s only shipped deliverable).
- `AGENTS.md` regenerates from `engine.py` with no diff.
- If any hook module is touched, `git diff` on it shows only docstring or literal-text lines and no predicate, exit code, or message-selection change.
- Bare suite `python3 -m pytest`, judged on the failing NODE ID delta against a baseline measured in the executing worktree, never on totals. AFTER minus BEFORE must be EMPTY. Do NOT copy a baseline from `ao1rb7` or `kbqpkn`: both cite figures that are now wrong, and `kbqpkn`'s own V-06 records that its predecessor's cited failure did not reproduce because the environmental cause (~189 untracked `opencode-recovery/*.md` files) is absent in a lane worktree. Measure your own.
  MEASURED IN THIS LANE AT REVIEW, so the executor knows what to expect and does not chase it: `1 failed, 7942 passed, 3 skipped, 2 xfailed, 3 warnings in 110.57s`, the single failure being `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`. It is ENVIRONMENTAL AND PRE-EXISTING, not this plan's: the assertion is `'OPENCODE_CONFIG_CONTENT' not in main_env` (`tests/test_turn_bounds.py:310`), and that variable is present in THIS AGENT SESSION's ambient environment, so the non-isolated env inherits it. It reproduces standalone (`1 failed` when run alone) and NOTHING in this plan's fence can affect it. Note this is a DIFFERENT failure from the `test_reporting_contract.py` one both siblings cite, which did NOT reproduce here; that is further reason to measure your own rather than reuse any figure in this Set.
- `pre-commit run --all-files`. MEASURED AT REVIEW: ALL TEN HOOKS PASS, including `ruff-format`. The claim that a pre-existing `ruff-format` failure exists on `tests/test_cli_output_docs_rollout.py` is STALE and was CORRECTED HERE: that file reports "1 file already formatted" and the full hook run reports `ruff-format ... Passed`. WHY THE STALE CLAIM IS MISLEADING RATHER THAN MERELY OUT OF DATE: a bare `python3 -m ruff format --check .` DOES report 92 files needing reformatting, because the ambient `ruff` is 0.16.3 while `.pre-commit-config.yaml:43` pins `rev: v0.4.4` and the hook also carries an `exclude:` (`:49`). So judge this hook by RUNNING THE HOOK, never by running ambient `ruff`, and do not pre-authorize ignoring a `ruff-format` failure that no longer exists: if one appears, it is probably yours.

## Spec / documentation sync

- NO SPEC AMENDMENT IS INTENDED, so no `.spec.md` path is declared in `Scope-Paths`. If E-03 finds that a shipped sentence contradicts a spec rather than the code, STOP and record it: amending a spec is a contract change that must be declared in `Scope-Paths` before the run starts (both runners announce declared spec edits up front and reconcile them at finalize), so it needs a new plan rather than an undeclared edit here.
- `AGENTS.md` is documentation OUTPUT, not a source: any correction goes in `engine.py` and is regenerated (E-04 check 3).
- Spec `77tr3o` R-5 shape (b) governs the retirement skip this plan exists because of. This plan CONSUMES that spec and does not amend it.

## Open questions

### OQ-01: Does correcting a sentence inside a terminal sibling's territory need a corrective IPD instead?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: A POLICY QUESTION ABOUT AUTHORING RULES, not an obligation this plan incurs. It becomes moot in the expected case (zero corrections, because `kbqpkn` wired nothing), and in the unexpected case E-03 already prescribes the fallback (file a corrective IPD), so no work is left unrecorded either way. A carrier would assert a pending task where what exists is a convention a maintainer may tighten.
- Resolution or deferral rationale: NARROWED AT REVIEW 2026-09-21, and the narrowing matters because the question as posed was wider than the decision actually outstanding. TWO CASES SPLIT APART. For the FOUR DRIVER-PROMPT FILES the answer is now settled and needs no maintainer: they are NOT declared in this plan's `Scope-Paths`, so a correction there is a corrective IPD by construction and E-02 only judges them (recorded under Deferred). What remains open is ONLY the five DECLARED paths, where this plan does hold edit authority and the policy tension is real. NON-BLOCKING because the expected correction count is ZERO (`kbqpkn` wired nothing, so every "OPT-IN" string stays true) and because E-03 already states the fallback: if a correction is large enough to need its own review, file a corrective IPD and record that decision instead of making the edit here. The tension is real and worth a ruling eventually: `ao1rb7`'s scope check says a fix belongs "in the OWNING child's fence", but both children will be `executed` when this runs and AGENTS.md forbids adding commits to an executed plan, so the owning fence is closed by construction. This plan resolves that by declaring both halves' paths itself, which is the only route that does not either edit an executed plan or leave a false sentence shipped. A maintainer may prefer a stricter rule (always file a corrective IPD, never touch a terminal sibling's files from a later child); if so, E-03's fallback branch is the one to make mandatory.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the full disclosure table with one row per site, each row carrying the QUOTED sentence and its `file:line` and a verdict. It must cover THREE sites for each of the four opt-in gates (module docstring, printed refusal text, `engine.create_*_hook` docstring) and TWO for each of the two wired gates (module docstring, printed refusal text), plus the two `.pre-commit-config.yaml` comment-block disclosures (`:70-71`, `:75-77`). A table carrying a third row for a WIRED gate is WRONG and fails this item, because no such installer exists (F-08); so is a table that silently drops the wired gates or the config disclosures. ALSO paste the re-measured `grep -ci opt-in` counts per hook module and compare them to the 0/0/3/3/2/2 partition recorded in this plan's Findings, naming any difference. A blanket "the disclosures are fine" does NOT satisfy this item; the sentences must be quoted. State the correction count explicitly, and if it is zero, say so as a positive finding rather than leaving it implied.
  - Observed evidence: PERFORMED BY: agent-executed child (`opencode its_direct/pt3-claude-opus-5-1m-us`), run `run-20260923T024621Z-3869306` position 31, lane worktree on branch `aw/lane/2s0iym` at base HEAD `22cf67d9`.

    CORRECTION COUNT: **ZERO**, stated as a positive finding. Every disclosure enumerated below accurately describes a bypassable local check. `kbqpkn` wired nothing, so every "OPT-IN" string remained true and no edit was warranted; per the parent's E-05 ("DO NOT 'FIX' THE DISCLOSURES IF YOU WIRE NOTHING") editing them would have manufactured the very drift this item guards against.

    RE-MEASURED PARTITION, `grep -ci opt-in` per hook module (note: the loop below iterates `agent_workflows/hooks/*.py`, so `__init__.py` appears and is IGNORED per E-01; there are SIX gate modules, not seven):

    ```
    $ for f in agent_workflows/hooks/*.py; do printf '%s %s\n' "$f" "$(grep -ci 'opt-in' "$f")"; done
    agent_workflows/hooks/backlog_blocking_close_gate.py 2
    agent_workflows/hooks/executed_transition_gate.py 0
    agent_workflows/hooks/__init__.py 0
    agent_workflows/hooks/ipd_dependency_statement_gate.py 3
    agent_workflows/hooks/precommit_scope_gate.py 3
    agent_workflows/hooks/prepush_authorization_gate.py 2
    agent_workflows/hooks/status_untooled_gate.py 0
    ```

    Reduced to the partition this plan's Findings record: `executed_transition_gate.py` 0, `status_untooled_gate.py` 0 (the two WIRED gates), `ipd_dependency_statement_gate.py` 3, `precommit_scope_gate.py` 3, `backlog_blocking_close_gate.py` 2, `prepush_authorization_gate.py` 2 (the four OPT-IN gates). **0/0/3/3/2/2, IDENTICAL to F-03's recorded partition. NO DIFFERENCE.**

    DISCLOSURE TABLE. Sixteen rows: three per opt-in gate (module docstring, printed refusal text, `engine.create_*_hook` installer docstring) = 12, two per wired gate (module docstring, printed refusal text) = 4, plus the two `.pre-commit-config.yaml` comment-block disclosures. No third row is fabricated for a wired gate (F-08: `engine.py` defines exactly four `create_*_gate_hook` installers and none for the two wired gates).

    | # | Gate | Site | `file:line` | Quoted sentence | Verdict |
    |---|---|---|---|---|---|
    | 1 | `executed_transition_gate` (WIRED) | module docstring | `agent_workflows/hooks/executed_transition_gate.py:24-26` | "Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`. This is a PREVENTION layer, not an absolute gate; the deterministic local backstop is the `proclint` detector (`aw check`/`aw doctor`). There is deliberately NO remote/CI enforcement." | ACCURATE. Names local-only, not-cloned, `--no-verify`-skippable, explicitly "not an absolute gate", and disclaims CI. |
    | 2 | `executed_transition_gate` (WIRED) | printed refusal text | `agent_workflows/hooks/executed_transition_gate.py:403-404` | "(This is a LOCAL best-effort hook; `--no-verify` bypasses it and the local `aw check`/`aw doctor` proclint detector is the backstop.)" | ACCURATE. The refusal itself discloses its own bypass at the moment an operator reads it. |
    | 3 | `status_untooled_gate` (WIRED) | module docstring | `agent_workflows/hooks/status_untooled_gate.py:15-20` | "Honest limits (never oversold): this is PREDICATE A (textual) - it catches only the CARELESS omission (a status flip with no note added). It does NOT catch a hand-edit that also writes a plausible history line; that limit is accepted (this is a safety net, the preventive layer is the `aw set` delegation + the `ipdgates` gates). Git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`. There is deliberately NO remote/CI enforcement (local only, mirroring Order dulzpy's human decision)" | ACCURATE, and stronger than required: it discloses a SECOND limit (the predicate is textual and a plausible-looking history line evades it) beyond the generic bypass. |
    | 4 | `status_untooled_gate` (WIRED) | printed refusal text | `agent_workflows/hooks/status_untooled_gate.py:61-62` | "(This is a LOCAL best-effort hook; `--no-verify` bypasses it, a hand-edit that also adds a plausible history line evades it, and `aw check`/`aw doctor` is the backstop.)" | ACCURATE. Carries both limits into the refusal text. |
    | 5 | `ipd_dependency_statement_gate` (OPT-IN) | module docstring | `agent_workflows/hooks/ipd_dependency_statement_gate.py:1` | "OPT-IN local pre-commit gate: refuse a staged IPD with an invalid/cyclic cross-IPD dependency statement" | ACCURATE. Opens with OPT-IN; matches `EXEMPT_OPT_IN` in `tests/test_gate_wiring.py:84` and its zero occurrences in the config. |
    | 6 | `ipd_dependency_statement_gate` (OPT-IN) | module docstring (honest limits) | `agent_workflows/hooks/ipd_dependency_statement_gate.py:21-23` | "Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`. There is deliberately NO CI enforcement here; the portable authority is child-02's `aw check` rule (+ CI). This is a best-effort local bypass-catcher, not the primary control." | ACCURATE. "not the primary control" is the honest form. |
    | 7 | `ipd_dependency_statement_gate` (OPT-IN) | printed refusal text | `agent_workflows/hooks/ipd_dependency_statement_gate.py:147-148` | "(This is a LOCAL best-effort OPT-IN hook; `--no-verify` bypasses it, it is not cloned by default, and `aw check`/CI is the portable authority.)" | ACCURATE. |
    | 8 | `ipd_dependency_statement_gate` (OPT-IN) | installer docstring | `agent_workflows/engine.py:5610-5616` (`create_dependency_gate_hook`, def at `:5603`) | "OPTIONALLY (opt-in) wire the ipd-dependency-statement pre-commit hook into a TARGET repo ... NOT called by the default setup path: the hook is installed ONLY on an explicit ``install=True`` request" | ACCURATE. States non-default installation as a property of the installer. |
    | 9 | `precommit_scope_gate` (OPT-IN) | module docstring | `agent_workflows/hooks/precommit_scope_gate.py:1` | "OPT-IN local pre-commit gate: run the shared checker over the staged commit and TEACH the fix" | ACCURATE. |
    | 10 | `precommit_scope_gate` (OPT-IN) | module docstring (honest limits) | `agent_workflows/hooks/precommit_scope_gate.py:16-19` | "Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with ``--no-verify``. This is OPT-IN best-effort FEEDBACK, not an authority boundary; the authoritative boundary is phase-5 CI running the same engine." | ACCURATE, and it is the canonical honest form: "not an authority boundary" stated in as many words. |
    | 11 | `precommit_scope_gate` (OPT-IN) | printed refusal text | `agent_workflows/hooks/precommit_scope_gate.py:66-68` | "(This is a LOCAL best-effort OPT-IN hook; `--no-verify` bypasses it, it is not cloned by default, and it is NOT an authority boundary - the authoritative gate is `aw check` in required CI.)" | ACCURATE. |
    | 12 | `precommit_scope_gate` (OPT-IN) | installer docstring | `agent_workflows/engine.py:5755-5756` (`create_precommit_scope_gate_hook`, def at `:5752`) | "OPT-IN wire the Phase-4 pre-commit scope/invariant gate (agentadhere diundn E-01). Idempotent, no-clobber, opt-in-only (never default-installed)." | ACCURATE. |
    | 13 | `backlog_blocking_close_gate` (OPT-IN) | module docstring (honest limits) | `agent_workflows/hooks/backlog_blocking_close_gate.py:25-29` | "Honest limits (never oversold): git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`. This hook is OPT-IN (NOT installed by default) - the authoritative, portable boundary is the child-02 `aw check` rule (`check.blocking-item-closed-without-gate`) + CI ..., never the local hook alone." | ACCURATE. "never the local hook alone" is explicit. NOTE: this module's line 1 says "Local pre-commit gate" WITHOUT the "OPT-IN" prefix its three siblings carry; that is a CONSISTENCY observation, not an inaccuracy, because the same docstring states OPT-IN at `:26`. Judged ACCURATE and left unedited (see the E-03 judgement and DECISION 31-2s0iym-D1). |
    | 14 | `backlog_blocking_close_gate` (OPT-IN) | printed refusal text | `agent_workflows/hooks/backlog_blocking_close_gate.py:74-75` | "(This is a LOCAL best-effort, OPT-IN hook; `--no-verify` bypasses it; the portable authority is the `aw check` rule + CI.)" | ACCURATE. |
    | 15 | `backlog_blocking_close_gate` (OPT-IN) | installer docstring | `agent_workflows/engine.py:5511-5518` (`create_backlog_close_gate_hook`, def at `:5504`) | "OPTIONALLY (opt-in) wire the backlog-blocking-close pre-commit hook into a TARGET repo ... NOT called by the default setup path: the hook is installed ONLY on an explicit ``install=True`` request (an operator opt-in / flag)" | ACCURATE. |
    | 16 | `prepush_authorization_gate` (OPT-IN) | module docstring | `agent_workflows/hooks/prepush_authorization_gate.py:1-12` | "OPT-IN local pre-push gate ... This hook is CONVENIENCE / FEEDBACK ONLY - it is explicitly NOT an authority boundary. A local pre-push hook is not cloned by default, is skippable with ``--no-verify``, and its acknowledgement signal (the ``AW_PUSH_AUTHORIZED`` env var) is visible to and settable by the agent, so it provides NO independent authorization ... The AUTHORITATIVE control ... is a protected remote branch / required CI / brokered credential" | ACCURATE, and the most complete disclosure in the set: it names the third, subtler limit (its own ack signal is agent-settable, so it is not independent authorization). |
    | 17 | `prepush_authorization_gate` (OPT-IN) | printed refusal text | `agent_workflows/hooks/prepush_authorization_gate.py:62-65` | "(HONEST LIMIT: this is a LOCAL, OPT-IN, bypassable (`--no-verify`) FEEDBACK hook, NOT an authority boundary and NOT independent authorization - a local env ack is settable by the agent. Real push authorization is a protected branch / required CI / brokered credential.)" | ACCURATE. |
    | 18 | `prepush_authorization_gate` (OPT-IN) | installer docstring | `agent_workflows/engine.py:5771-5772` (`create_prepush_authorization_gate_hook`, def at `:5768`) | "OPT-IN wire the Phase-4 pre-push authorization FEEDBACK gate (agentadhere diundn E-02). Idempotent, no-clobber, opt-in-only. HONEST: feedback only, not an authority boundary." | ACCURATE. |
    | 19 | (config, wired gates) | `.pre-commit-config.yaml` comment block | `.pre-commit-config.yaml:70-71` | "Best-effort/local only (skippable with --no-verify); the deterministic backstop is the local proclint detector via `aw check`/`aw doctor`. No CI enforcement." | ACCURATE. |
    | 20 | (config, wired gates) | `.pre-commit-config.yaml` comment block | `.pre-commit-config.yaml:75-77` | "Honest limit: `pre-merge-commit` does NOT run for a fast-forward merge (no commit is created) or on the conflicted-then-resolved path (git runs prepare-commit-msg/commit-msg, and the final `git commit` there is covered by `pre-commit`)." | ACCURATE. Names the exact two paths the stage misses rather than implying blanket merge coverage. The sibling block at `:90-92` carries the same honest limit for the untooled-status gate ("Best-effort/local only (skippable with --no-verify; a hand-edit that also adds a plausible history line evades it); the deterministic backstop is `aw check`/`aw doctor`. No CI enforcement."), also ACCURATE. |

    The two extra rows beyond the mandated sixteen (#6 and #10 split a gate's OPT-IN opener from its "Honest limits" paragraph inside the SAME module docstring) are additional detail within the required site classes, not a fabricated installer row for a wired gate. Every wired-gate row set is exactly TWO sites (#1-#2 and #3-#4).

    ENUMERATION WAS NOT DONE BY GREPPING `opt-in` ALONE, per E-01: the module docstrings were extracted whole with `ast.get_docstring`, the refusal texts read from each `main()`, and the installers located with `grep -n '^def create_.*gate_hook' agent_workflows/engine.py` (four results: `:5504`, `:5603`, `:5752`, `:5768`; none for the two wired gates, confirming F-08).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste every Order 02 contract sentence with its `file:line`, including an explicit verdict on the `engine.py:1320` "immune to this by construction" claim (present at HEAD, so it must be addressed either as corrected, narrowed by Order 02, or judged accurate with the reason). THE VERDICT MUST NAME THE ANTECEDENT of "this" and cite the mechanism it was judged against (`git_commit_helper.offer_commit`), because a verdict that reads "immune" as a general hook-bypass claim is judging a sentence the block does not contain (F-15); an "inaccurate" verdict specifically requires a demonstration that the tooled path can commit an unnamed path. ALSO paste the four DRIVER-PROMPT sentences, located BY STRING and not by `y9vpvv`'s stale line numbers, with their real `file:line` and a verdict each (F-10). Paste the comparison showing the generator prose and the rendered `AGENTS.md` prose agree. State whether Order 02's descriptive retry sentence shipped, and since `lqly9m` is now `executed`, justify any withholding as a finding rather than as the expected path.
  - Observed evidence: PERFORMED BY: agent-executed child, same run/lane as V-01.

    CORRECTION COUNT FOR THIS HALF: **ZERO** edits made. One finding raised and reported rather than edited (see the stale `work_cmd.py` sentence below, backlog `qkptz2`).

    THE `engine.py:1320` SUBJECT IS GONE, AND THAT IS THE CORRECT OUTCOME RATHER THAN A MISSING VERDICT. The plan and its review both recorded "immune to this by construction" as live at HEAD `41f6a45b`. It is NOT live at this lane's base `22cf67d9`:

    ```
    $ grep -n 'immune to this by construction' agent_workflows/engine.py AGENTS.md
    (no output)
    ```

    Order 02 REPLACED it. `git show --stat 12ecd491` ("feat(commit): add a plan-less aw commit and land the ruled MUST wording (y9vpvv)") touched `AGENTS.md`, `agent_workflows/engine.py`, `agent_workflows/cli.py`, `agent_workflows/work_cmd.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/runner_shared.py`, `tests/test_work_commit.py`. So E-02's mandated verdict on that sentence is: **SUPERSEDED BY ORDER 02, replaced by the ruled MUST wording below.** The antecedent analysis F-15 prescribed is preserved and applied to the REPLACEMENT sentence, because the replacement inherits the same mechanism claim.

    ORDER 02's SHIPPED CONTRACT SENTENCES, quoted with `file:line` and judged.

    | # | `file:line` | Quoted sentence | Verdict |
    |---|---|---|---|
    | 1 | `agent_workflows/engine.py:1385-1387` (generator) / `AGENTS.md:75` (rendered) | "USE THE TOOLED COMMIT PATH. You MUST commit through `aw commit`, not raw `git commit`." | ACCURATE AS AN INSTRUCTION, and it makes NO enforcement claim. This is the MUST that F-15 warned could "invite the reading that the tooled path is enforced when it is not". It does not: the sentence is a directive to the reader, and the block never says a mechanism compels it. The honest limit E-02 told me to check for the ABSENCE of ("`aw commit` is a CONVENIENCE WRAPPER, not an authority boundary; nothing prevents an agent from running raw `git`") is indeed ABSENT AS A SENTENCE, but it is NOT NEEDED, because the block's own next clause concedes the wrapper can be declined: "If no form of `aw commit` fits your case, you MUST say so explicitly in your report, naming what you ran and why". A contract that provides a DECLARED ESCAPE HATCH cannot be read as claiming enforcement; it is a protocol obligation, exactly the shape the block uses for the integration lock ("THIS IS A PROTOCOL, NOT AN ENFORCEMENT BOUNDARY"). Judged ACCURATE. |
    | 2 | `agent_workflows/engine.py:1385-1388` / `AGENTS.md:75` | "It snapshots the index BEFORE staging, stages only your explicit paths, commits only the intersection of those paths with what it itself staged, and on any failure resets ONLY its own paths, so a co-worker's restored path can never enter your commit." | ACCURATE AS SCOPED. THE ANTECEDENT of the "can never" claim is the PRECEDING paragraph's hazard, index pollution sweeping a co-worker's staged edit into your commit (`engine.py:1354-1361`, the "RE-VERIFY AFTER A FAILED RAW COMMIT" paragraph, whose own subject is a `pre-commit` stash-restore leaving "paths you never staged sitting in the index"), NOT hook bypass in general. VERIFIED AGAINST THE MECHANISM, four clauses one at a time in `git_commit_helper.offer_commit` (`git_commit_helper.py:470`): (a) "snapshots the index BEFORE staging" -> `pre_staged = set(_staged_paths(repo_root))` computed BEFORE the `git add` (`:579`); (b) "stages only your explicit paths" -> `git add -- <add_paths>` where `add_paths` is derived from `rel_paths` alone (`:638-642`), and the docstring states "ONLY these are ever staged"; (c) "commits only the intersection" -> `our_staged = sorted(now_staged & set(rel_paths))` (`:652`), then that set alone is committed; (d) "on any failure resets ONLY its own paths" -> `_git(repo_root, ["reset", "--quiet", "HEAD", "--", *our_staged])` on every non-success path (`:695`) and `*rel_paths` on the add-failure path (`:645`). The docstring also states the invariant directly: "In BOTH modes a path outside ``paths`` is NEVER staged by this helper." THE FALSIFICATION CRITERION E-02 SET (a demonstration that the tooled path can commit a path the caller did not name) IS NOT MET, and the repository ships the non-vacuous proofs: `tests/test_git_commit_helper.py::test_commits_only_requested_paths_leaving_unrelated_dirty`, `::test_on_unrelated_staged_scope_leaves_unrelated_staged`, `::test_on_unrelated_staged_refuse_commits_nothing`, `::test_trailers_do_not_widen_scope_or_stage_extra`, plus `tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_still_excludes_a_co_workers_staged_file` whose docstring names this exact property ("THE PROTECTION THAT MUST NOT WEAKEN"). All pass (output below). |
    | 3 | `agent_workflows/engine.py:1388-1390` / `AGENTS.md:75` | "When a MUTATING hook rewrites one of your own paths and rejects, it re-stages that path and retries ONCE, so whitespace or format churn costs you no round trip and no re-verify." | ACCURATE. This is Order 02's DESCRIPTIVE RETRY SENTENCE and it **DID SHIP** (E-02 asked explicitly, since `lqly9m` is `executed` and a withheld sentence would have been a finding: nothing was withheld). Verified against `commit_lock.commit_isolated` (`commit_lock.py:221`), whose docstring says "ONE BOUNDED RETRY WHEN A HOOK REWROTE OUR OWN PATHS, and NEVER when a hook merely refused", implemented by hashing our paths after the `git add` and re-hashing on rejection (`:355-361`), re-adding and retrying exactly once (`:409-419`). `offer_commit` routes through it (`git_commit_helper.py:667`). Shipped proofs, all passing: `tests/test_commit_lock.py::test_a_hook_rewrite_is_classified_and_retried_exactly_once`, `::test_a_hook_refusal_is_not_retried_and_behaves_exactly_as_before`, `::test_a_second_rejection_after_the_retry_still_fails`. The "ONCE" is real and bounded, so the sentence does not overclaim a loop. |
    | 4 | `agent_workflows/engine.py:1390-1392` / `AGENTS.md:75` | "If no form of `aw commit` fits your case, you MUST say so explicitly in your report, naming what you ran and why, and re-verify the staged set as above." | ACCURATE, and load-bearing for row 1's verdict: it is the declared escape hatch that keeps the MUST a protocol rather than an asserted boundary. (This turn EXERCISES it; see the E-03 evidence and DECISION 31-2s0iym-D2.) |
    | 5 | `agent_workflows/engine.py:1395-1396` / `AGENTS.md` execution contract | "commit ONLY files you changed, limited to the paths you name, through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change), never `git add -A`/bare/`-a`, and never push" | ACCURATE. Both tooled forms exist: `aw commit --no-plan -m <msg> -- <paths>` is what Order 02's E-01..E-03 added, and its 14 shipped cases pass (output below). |

    THE FOUR DRIVER-PROMPT SITES, LOCATED BY STRING NOT BY LINE NUMBER (F-10 warned `y9vpvv`'s cited numbers were stale; they are stale again, which is exactly why locating by string was mandated). E-02 told me to search for `git commit -m msg -- <path>`. THAT STRING IS NOW ABSENT from all three runner modules, because Order 02's E-09 replaced the raw-`git commit` instruction with the tooled one:

    ```
    $ grep -rn 'git commit -m msg' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py agent_workflows/engine.py
    agent_workflows/oc_runipd.py:0
    agent_workflows/agy_runipd.py:0
    agent_workflows/runner_shared.py:0
    agent_workflows/engine.py:0
    ```
    (counts from `grep -rc`; zero in every file.)

    So the four sites were re-located by the string Order 02 actually shipped, `aw commit`:

    ```
    $ grep -rn 'aw commit' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py
    agent_workflows/oc_runipd.py:2178:4. Commit only files you changed, limited to the paths you name, through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change).
    agent_workflows/agy_runipd.py:2118:4. Commit only files you changed, limited to the paths you name, through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change).
    agent_workflows/runner_shared.py:22223:   - If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change), limited to the paths you name. Never push.
    agent_workflows/runner_shared.py:22316:   - If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change), limited to the paths you name. Never push.
    ```

    Exactly FOUR sites, matching Order 02's "Zero sites remain" claim in commit `12ecd491`. VERDICT ON EACH: **ACCURATE.** Each states the requirement and names both tooled forms; none claims the path is enforced, and none instructs raw `git commit` as the method. Their real `file:line` values are `oc_runipd.py:2178`, `agy_runipd.py:2118`, `runner_shared.py:22223`, `runner_shared.py:22316` (the review-measured `3261`/`2085`/`14781`/`14874` are stale, as F-10 predicted of any line number in this Set).

    SOURCE AND RENDERED `AGENTS.md` AGREE. The generator prose was extracted by CALLING the generator, and compared against the on-disk block:

    ```
    $ python3 -c "import sys; sys.path.insert(0,'.'); from agent_workflows import engine; import pathlib;
    live=pathlib.Path('AGENTS.md').read_text();
    i=live.index('<!-- aw:block -->'); j=live.index('<!-- /aw:block -->')+len('<!-- /aw:block -->');
    print('live block == generated:', live[i:j].strip()==engine.agents_managed_block(target_layout='aw').strip())"
    live block == generated: True
    ```

    and the rendered sentence is byte-present in the file agents actually read:

    ```
    $ grep -n 'USE THE TOOLED COMMIT PATH' AGENTS.md
    75:USE THE TOOLED COMMIT PATH. You MUST commit through `aw commit`, not raw `git commit`. It snapshots the index BEFORE staging, stages only your explicit paths, commits only the intersection of those paths with what it itself staged, and on any failure resets ONLY its own paths, so a co-worker's restored path can never enter your commit. When a MUTATING hook rewrites one of your own paths and rejects, it re-stages that path and retries ONCE, so whitespace or format churn costs you no round trip and no re-verify. If no form of `aw commit` fits your case, you MUST say so explicitly in your report, naming what you ran and why, and re-verify the staged set as above.
    ```

    So there is no corrected-in-generator-but-never-regenerated hazard here: generator and rendered copy are equal, proven by the shipped assertion in V-04 as well.

    PASSING MECHANISM PROOFS, actual runner output:

    ```
    $ python3 -m pytest tests/test_work_commit.py -o addopts="" -v
    collected 14 items
    tests/test_work_commit.py::PlanLessCommitJsonShapeTest::test_the_flag_is_declared_and_documented PASSED [  7%]
    tests/test_work_commit.py::PlanLessCommitJsonShapeTest::test_the_verb_still_reports_a_machine_readable_surface PASSED [ 14%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_stages_only_the_named_paths PASSED [ 21%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_commits_every_path_after_the_marker PASSED [ 28%]
    tests/test_work_commit.py::PlanLessCommitTest::test_the_plan_bearing_form_is_unchanged PASSED [ 35%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_routes_through_the_one_shared_commit_helper PASSED [ 42%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_records_the_requested_message_verbatim PASSED [ 50%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_still_excludes_a_co_workers_staged_file PASSED [ 57%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_honors_no_commit_as_a_preview PASSED [ 64%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_without_a_message_is_a_usage_error PASSED [ 71%]
    tests/test_work_commit.py::PlanLessCommitTest::test_a_contradictory_invocation_is_a_usage_error PASSED [ 78%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_commits_a_path_no_plan_governs PASSED [ 85%]
    tests/test_work_commit.py::PlanLessCommitTest::test_no_plan_names_the_protections_it_skips PASSED [ 92%]
    tests/test_work_commit.py::PlanLessCommitTest::test_omitting_both_a_plan_and_the_flag_still_refuses PASSED [100%]
    ============================== 14 passed in 1.69s ==============================

    $ python3 -m pytest tests/test_commit_lock.py -o addopts="" -k 'hook_rewrite_is_classified_and_retried_exactly_once or hook_refusal_is_not_retried or second_rejection_after_the_retry'
    collected 22 items / 19 deselected / 3 selected
    tests/test_commit_lock.py ...                                            [100%]
    ======================= 3 passed, 19 deselected in 0.31s =======================

    $ python3 -m pytest tests/test_git_commit_helper.py -o addopts="" -k 'unrelated or staged or scope or intersect' -v
    collected 59 items / 51 deselected / 8 selected
    tests/test_git_commit_helper.py::test_commits_only_requested_paths_leaving_unrelated_dirty PASSED [ 12%]
    tests/test_git_commit_helper.py::test_uses_path_scoped_add_and_commit_argv PASSED [ 25%]
    tests/test_git_commit_helper.py::test_on_unrelated_staged_scope_leaves_unrelated_staged PASSED [ 37%]
    tests/test_git_commit_helper.py::test_invalid_on_unrelated_staged_raises PASSED [ 50%]
    tests/test_git_commit_helper.py::test_trailers_do_not_widen_scope_or_stage_extra PASSED [ 62%]
    tests/test_git_commit_helper.py::test_refuse_ignores_unrelated_when_none_staged PASSED [ 75%]
    tests/test_git_commit_helper.py::test_on_unrelated_staged_refuse_commits_nothing PASSED [ 87%]
    tests/test_git_commit_helper.py::test_staged_paths_reports_both_sides_of_a_rename PASSED [100%]
    ======================= 8 passed, 51 deselected in 0.57s =======================
    ```

    ONE FINDING, REPORTED NOT EDITED (it is a stale internal comment, not a shipped contract sentence, and it lies OUTSIDE this plan's `Scope-Paths`). `agent_workflows/work_cmd.py:422-423` still says agent commits "are made by the agent running raw `git commit -m msg -- <path>` per the runbook directive, pass through no `offer_commit` call". That runbook directive NO LONGER EXISTS: Order 02's E-09 removed it from all four driver-prompt sites (measured above, zero occurrences), so the comment's factual premise about what the runner instructs is now false, and a reader using it to reason about trailer attribution would be misled about WHY attribution is still missing. It is not a Set honesty violation in the sense E-03 governs (it describes no guard as a boundary; it is an under-claim about tooling reach, and the deferred attribution gap it documents remains genuinely open). Filed as backlog `t5ycse` (`.aw/records/backlog/open/20260923-trailerdoc-01-t5ycse-stale-runbook-directive-comment-in-trailers-docstr.backlog.md`). NOT edited here: `agent_workflows/work_cmd.py` is not a declared path, and E-02's own rule for an out-of-fence untruth is "a FINDING TO REPORT, not an edit to make here".
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the explicit cross-half judgement: a statement that no sentence shipped by this Set describes a bypassable guard as an authority boundary, OR each offending sentence quoted with its correction and the owning child named. The judgement must reference BOTH halves together (a per-file pass is not a Set-wide claim). If any sentence was corrected, paste the `git diff` for it and confirm no predicate, exit code, or message-selection logic changed. If a correction was deferred to a corrective IPD, name that IPD.
  - STATE WHO PERFORMED THIS ITEM AND IN WHAT MODE (agent-executed child, or human). This child exists precisely so that the answer is never "nobody"; recording the performer is what distinguishes this from the parent's unperformable E-03.
  - Observed evidence: PERFORMED BY, stated because this is the whole reason the plan exists and the answer must never be "nobody": **an agent-executed child**, `opencode its_direct/pt3-claude-opus-5-1m-us`, driven by `aw oc run` as run `run-20260923T024621Z-3869306` queue position 31, in the isolated lane worktree on branch `aw/lane/2s0iym` at base HEAD `22cf67d9`. Not a human, not a retiring orchestrator, and NOT skipped: this evidence passes through the pre-transition E/V checkpoint that `retire_orchestrator` omits (`ipd_lifecycle.ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]`), which is precisely the gap F-02 recorded.

    THE SET-WIDE JUDGEMENT, stated as a property of both halves together rather than as a per-file pass:

    > **NO SENTENCE SHIPPED OR PRESERVED BY THE `commitguard` SET DESCRIBES A BYPASSABLE GUARD AS AN AUTHORITY BOUNDARY.** Order 01 (`kbqpkn`) shipped `tests/test_gate_wiring.py` and wired nothing, preserving twenty disclosure sites (V-01) every one of which names its local-only, not-cloned, `--no-verify`-skippable character, four of them in the words "not an authority boundary" and the rest in equivalent terms ("not an absolute gate", "not the primary control", "never the local hook alone", "No CI enforcement"). Order 02 (`y9vpvv`) shipped a MUST directive plus a four-clause mechanism claim (V-02), and that claim is true as scoped: every clause was verified against `git_commit_helper.offer_commit` and `commit_lock.commit_isolated`, and the MUST is accompanied by a declared escape hatch, so it asserts an obligation on the reader rather than an enforced boundary. **ZERO CORRECTIONS WERE MADE, IN EITHER HALF.**

    THE CONCRETE CONTRADICTION E-03 NAMED WAS CHECKED AND IS ABSENT. The parent's cross-IPD section warned that Order 01's half makes gates FIRE while Order 02's wording promises the tooled path "costs no round trip", so that if a gate REFUSES rather than rewrites, a retry claim covering it would be false. The two halves do not collide, for a mechanical reason: Order 02's retry sentence is explicitly conditioned on a MUTATING hook ("When a MUTATING hook rewrites one of your own paths and rejects"), and `commit_lock.commit_isolated` classifies the two cases apart by re-hashing our paths, retrying ONLY on a rewrite and never on a bare refusal (`commit_lock.py:355-361`, docstring "ONE BOUNDED RETRY WHEN A HOOK REWROTE OUR OWN PATHS, and NEVER when a hook merely refused"). Order 01's two WIRED gates are exactly the refusing kind, and `executed_transition_gate.py:24-26` / `status_untooled_gate.py:15-20` describe themselves as refusing, never as rewriting. So the retry sentence does not reach them and does not claim to. Verified by the shipped pair `tests/test_commit_lock.py::test_a_hook_rewrite_is_classified_and_retried_exactly_once` and `::test_a_hook_refusal_is_not_retried_and_behaves_exactly_as_before`, both passing (pasted in V-02).

    THE INVERSE ASYMMETRY E-03 ALSO REQUIRED, created by Order 01 wiring nothing, WAS CHECKED AND IS ABSENT. The risk was Order 02's wording implying a gate protects the commit path when that gate is opt-in and not installed here. It does not: the tooled-path sentence attributes the protection entirely to `aw commit`'s OWN staging discipline (snapshot, explicit paths, intersection, scoped reset) and never to any hook, and the block's ONLY mention of an opt-in gate (`AGENTS.md:231-236`, `backlog-blocking-close-gate`) states "It is NOT installed by default" and "never the local hook alone" in the same paragraph. So a reader of Order 02's half cannot conclude that an uninstalled gate is guarding their commit.

    THE ONE PLACE THE TWO HALVES GENUINELY MEET, and it reinforces rather than contradicts: Order 02's block says of the integration lock "THIS IS A PROTOCOL, NOT AN ENFORCEMENT BOUNDARY ... it cannot stop a raw `git merge` typed by someone who does not [use it]", and then explains that a merge-blocking git hook is "DELIBERATELY not part of this: it would be local-only and skippable". That is Order 01's honest-limit thesis restated in Order 02's own prose, by the same reasoning, about a different mechanism. The two halves agree.

    NO `git diff` IS PASTED FOR A CORRECTION BECAUSE NO SENTENCE WAS CORRECTED, which is the outcome the plan predicted ("Most likely shipped diff: NONE") and the parent's E-05 required ("DO NOT 'FIX' THE DISCLOSURES IF YOU WIRE NOTHING"). No predicate, exit code, or message-selection logic was touched in any hook module; the working tree carries no change under `agent_workflows/hooks/`, `agent_workflows/engine.py`, `AGENTS.md`, `.pre-commit-config.yaml` or `tests/test_gate_wiring.py`:

    ```
    $ git status --porcelain -- agent_workflows/hooks/ agent_workflows/engine.py AGENTS.md .pre-commit-config.yaml tests/test_gate_wiring.py
    (no output)
    ```

    NO CORRECTION WAS DEFERRED TO A CORRECTIVE IPD, because none was needed. Two observations were recorded rather than edited, and neither is a Set honesty violation: (1) `backlog_blocking_close_gate.py:1` lacks the "OPT-IN" opener its three opt-in siblings carry, while stating OPT-IN at `:26` of the same docstring, so it is a cosmetic inconsistency and not an inaccurate sentence (DECISION 31-2s0iym-D1); (2) `work_cmd.py:422-423` cites a runbook directive Order 02 removed, which is an under-claim about tooling reach in a file outside this plan's fence, reported and filed as backlog `t5ycse` (DECISION 31-2s0iym-D3). Per OQ-01's narrowing, an edit in an undeclared path would require a corrective IPD; since the sentence is not a boundary overclaim, no corrective IPD is warranted and the backlog item is the correct carrier.

    OWNING-CHILD ATTRIBUTION, recorded even though the correction count is zero, so the Set's audit trail is complete: had a correction been needed, Order 01's territory is `agent_workflows/hooks/` + `.pre-commit-config.yaml` and Order 02's is `agent_workflows/engine.py` + `AGENTS.md` (regenerated, never hand-edited). Both children are `executed`, so neither fence could have received the commit, which is why this plan declares the union itself.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste (1) `.pre-commit-config.yaml`'s `default_install_hook_types` and `default_stages` lines plus `29wvmj`'s `pre-merge-commit` entry and comment block, with an explicit statement that they are byte-unchanged and that `pre-push`'s absence matches `kbqpkn`'s recorded decision, INCLUDING the installed-hook listing read from `"$(git rev-parse --git-common-dir)/hooks"` rather than `.git/hooks` (F-12); (2) the list of registered hook IDS with line numbers, distinguished from the `entry:` VERBS they invoke (F-11); (3) the `AGENTS.md` no-drift proof as the `tests/test_shared_checkout_contract.py` run naming `NoDriftTests::test_repo_agents_block_equals_generated` (F-07). A `merge_aw_block` round-trip diff does NOT satisfy this item and a near-empty diff from it is a FALSE PASS, because the consent layer preserves on-disk drift today; if you paste one, state that it is supplementary and that the shipped assertion is the proof. (4) the `tests/test_gate_wiring.py` run summary line. Also paste the bare-suite BEFORE and AFTER failing node id sets and show the delta is empty, using a baseline measured in this worktree rather than any figure cited in this Set's plans; the review-measured baseline (F-14) is a cross-check, not a substitute. FINALLY paste the `pre-commit run --all-files` result and, if `ruff-format` fails, treat it as YOURS rather than pre-authorized, since it passes at review (F-09).
  - Observed evidence: PERFORMED BY: agent-executed child, same run/lane as V-01..V-03.

    **CHECK 1, `.pre-commit-config.yaml` INTEGRITY.**

    ```
    $ grep -n 'default_install_hook_types\|default_stages' .pre-commit-config.yaml
    17:default_install_hook_types: [pre-commit, pre-merge-commit]
    23:default_stages: [pre-commit]
    ```

    `29wvmj`'s `pre-merge-commit` entry and its explanatory comment block, read whole:

    ```
    $ awk 'NR>=68 && NR<=84 {printf "%d: %s\n", NR, $0}' .pre-commit-config.yaml
    68:       # (integpath 29wvmj: the journal lives under gitignored .aw/state/, so it cannot travel with a
    69:       # lane branch and every integration of a genuinely finalized lane used to be refused).
    70:       # Best-effort/local only (skippable with --no-verify); the deterministic backstop is the local
    71:       # proclint detector via `aw check`/`aw doctor`. No CI enforcement.
    72:       #
    73:       # THE ONLY hook registered for `pre-merge-commit` as well as `pre-commit`, because that is the
    74:       # stage git runs for an AUTOMATED merge; without it an automated merge carrying a plan into
    75:       # executed/ is not gated at all. Honest limit: `pre-merge-commit` does NOT run for a
    76:       # fast-forward merge (no commit is created) or on the conflicted-then-resolved path (git runs
    77:       # prepare-commit-msg/commit-msg, and the final `git commit` there is covered by `pre-commit`).
    78:       - id: ipd-executed-transition-gate
    79:         name: no raw plan->executed commit (use aw ipd finalize)
    80:         entry: python3 -m agent_workflows ipd-executed-gate
    81:         language: system
    82:         pass_filenames: false
    83:         always_run: true
    84:         stages: [pre-commit, pre-merge-commit]
    ```

    BYTE-UNCHANGED, PROVEN BY GIT RATHER THAN BY EYE, and proven against the RIGHT baseline. The last commit to touch this file is `29wvmj`'s own, so a byte-comparison against it establishes that NEITHER Order 01 nor Order 02 modified the file at all:

    ```
    $ git log -1 --format='%h %s' -- .pre-commit-config.yaml
    bcd9755f fix(hooks): accept a finalized lane merge in the executed-transition gate (29wvmj)

    $ git diff bcd9755f HEAD --quiet -- .pre-commit-config.yaml && echo "IDENTICAL to bcd9755f (29wvmj)"
    IDENTICAL to bcd9755f (29wvmj)

    $ git diff HEAD --quiet -- .pre-commit-config.yaml && echo "and IDENTICAL to this lane's HEAD (this turn changed nothing)"
    and IDENTICAL to this lane's HEAD (this turn changed nothing)
    ```

    `pre-push`'s ABSENCE MATCHES `kbqpkn`'s RECORDED DECISION AND IS NOT AN OMISSION. `default_install_hook_types` holds exactly the two original entries; the parent's expectation of a third (`pre-push`) is STALE for the reason F-05 recorded, namely that `kbqpkn` wired nothing. The decision is durably recorded in `tests/test_gate_wiring.py:74`, which classifies `prepush-authorization-gate` as `EXEMPT_OPT_IN` with the citation "diundn OQ-01 RESOLVED - OPT-IN; declined kbqpkn OQ-01 2026-09-10" and the stated reason that it "refuses EVERY push lacking `AW_PUSH_AUTHORIZED=1` BY DESIGN, so wiring it is a workflow-posture choice, not a safety fix". So the absence is a decision with a carrier, checked mechanically by a passing test, not a gap.

    INSTALLED-HOOK LISTING READ FROM THE GIT COMMON DIR, per F-12, with the `.git/hooks` failure shown beside it so the two claims are not conflated:

    ```
    $ git rev-parse --git-common-dir
    <REPO>/.git        # the SHARED common dir, not this lane's per-worktree gitdir
                       # (absolute path redacted: the leak gate correctly refuses a home path here)

    $ ls "$(git rev-parse --git-common-dir)/hooks" | grep -v sample
    pre-commit

    $ ls .git/hooks
    ls: cannot access '.git/hooks': Not a directory
    ```

    The second command FAILS because this is a lane worktree where `.git` is a FILE. That failure is reported as an artifact of the worktree layout, NOT as evidence about installed hooks; the authoritative reading is the first one, a single installed `pre-commit` hook and no `pre-push`, which agrees with `kbqpkn` having wired nothing.

    **CHECK 2, WIRING-VERSUS-WORDING MECHANICAL INPUT.** The registered hook IDS, with line numbers, kept distinct from the `entry:` VERBS they invoke (F-11):

    ```
    $ grep -n '      - id:' .pre-commit-config.yaml
    29:      - id: trailing-whitespace
    31:      - id: end-of-file-fixer
    33:      - id: check-yaml
    34:      - id: check-added-large-files
    40:      - id: gitleaks
    45:      - id: ruff
    48:      - id: ruff-format
    56:      - id: local-leaks
    78:      - id: ipd-executed-transition-gate
    93:      - id: ipd-status-untooled-gate

    $ grep -n 'entry:' .pre-commit-config.yaml
    58:        entry: python3 -m agent_workflows check-local-leaks
    80:        entry: python3 -m agent_workflows ipd-executed-gate
    95:        entry: python3 -m agent_workflows ipd-status-untooled-gate
    ```

    So, said precisely: the two gate REGISTRATIONS are the ids `ipd-executed-transition-gate` (`:78`) and `ipd-status-untooled-gate` (`:93`); the ENTRY POINTS they invoke are the verbs `ipd-executed-gate` (`:80`) and `ipd-status-untooled-gate` (`:95`). `ipd-executed-gate` is a VERB, not an id, which is the trap `tests/test_gate_wiring.py:172` records ("the id is free text (`ipd-executed-transition-gate` runs the verb `ipd-executed-gate`) while the entry is what actually executes"). Note the second gate's id and verb happen to be the same string; the first gate's differ, which is why the distinction has to be stated rather than assumed.

    The four OPT-IN gates appear ZERO times in the config:

    ```
    $ grep -nci 'dependency-statement\|precommit-scope\|backlog-blocking-close\|prepush-authorization' .pre-commit-config.yaml
    0
    ```

    That is the mechanical input E-03 consumed: two gates registered, four absent, and every disclosure in V-01 consistent with exactly that partition.

    **CHECK 3, `AGENTS.md` REGENERATES WITH NO DIFF, PROVEN BY THE SHIPPED ASSERTION.** The `merge_aw_block` round-trip route was NOT used as the proof, because F-07 measured that it cannot detect a hand edit in this repository. Actual runner output:

    ```
    $ python3 -m pytest tests/test_shared_checkout_contract.py
    bringing up nodes...
    bringing up nodes...

    ..........                                                               [100%]
    10 passed in 2.04s
    ```

    The item within it that constitutes the proof is `tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated` (`:165-170`), which reads `AGENTS.md`, slices the `<!-- aw:block -->`..`<!-- /aw:block -->` span and asserts equality against `engine.agents_managed_block(target_layout="aw")` DIRECTLY, bypassing `_apply_section_consent` entirely and so immune to the drift-preservation defect.

    NON-VACUITY RE-CONFIRMED INDEPENDENTLY THIS TURN rather than taken from the review, by performing the same comparison against a corrupted copy in memory:

    ```
    $ python3 -c "...; live block == generated: ...; corrupted block == generated: ..."
    live block == generated: True
    corrupted block == generated: False (must be False => assertion is non-vacuous)
    ```

    (The corruption injected the literal `HAND-EDITED ` before `USE THE TOOLED COMMIT PATH` in the sliced block. The live block compares EQUAL and the corrupted one UNEQUAL, so the assertion genuinely discriminates and its pass is meaningful.)

    NO SUPPLEMENTARY `merge_aw_block` DIFF IS PASTED, deliberately: E-04 permits one only if labelled supplementary, and pasting a proof known to be blind to its own subject adds nothing but risk of misreading. The stale manifest hash was NOT touched (that is `y9vpvv`'s E-07, already landed separately as commit `91ba3d7c`; `.aw/system/managed-sections.json` is not a declared path here and this turn did not write it).

    **`tests/test_gate_wiring.py` PASSES AND IS STILL NON-VACUOUS.** Summary line plus the per-test enumeration, since its non-vacuity is asserted by named cases rather than assumed:

    ```
    $ python3 -m pytest tests/test_gate_wiring.py
    bringing up nodes...
    bringing up nodes...

    ..........                                                               [100%]
    10 passed in 2.06s

    $ python3 -m pytest tests/test_gate_wiring.py -o addopts="" -v
    collected 10 items
    tests/test_gate_wiring.py::WiredGateRegistrationTests::test_each_wired_gate_is_registered_for_its_declared_stages PASSED [ 10%]
    tests/test_gate_wiring.py::WiredGateRegistrationTests::test_each_wired_gate_uses_the_established_local_hook_shape PASSED [ 20%]
    tests/test_gate_wiring.py::WiredGateRegistrationTests::test_each_exempt_gate_is_absent_from_the_config PASSED [ 30%]
    tests/test_gate_wiring.py::WiredGateRegistrationTests::test_no_unclassified_packaged_verb_is_registered PASSED [ 40%]
    tests/test_gate_wiring.py::GateClassificationTests::test_a_removed_gate_verb_fails PASSED [ 50%]
    tests/test_gate_wiring.py::GateClassificationTests::test_an_unclassified_new_gate_verb_fails PASSED [ 60%]
    tests/test_gate_wiring.py::GateClassificationTests::test_every_exemption_carries_a_reason_and_citation PASSED [ 70%]
    tests/test_gate_wiring.py::GateClassificationTests::test_every_discovered_gate_verb_is_classified PASSED [ 80%]
    tests/test_gate_wiring.py::GateVerbDiscoveryTests::test_discovery_is_not_vacuous PASSED [ 90%]
    tests/test_gate_wiring.py::GateVerbDiscoveryTests::test_discovery_finds_a_gate_verb_for_every_hook_module PASSED [100%]
    ============================== 10 passed in 0.60s ==============================
    ```

    NON-VACUITY IS CONFIRMED RATHER THAN ASSUMED, and it is structural rather than my assertion: `test_discovery_is_not_vacuous` proves the verb set is discovered by the `agent_workflows.hooks` import rather than by name, `test_an_unclassified_new_gate_verb_fails` feeds the pure `classify()` function a SYNTHETIC SEVENTH GATE and requires a violation (so the guard against an unclassified new gate is proven to fire without perturbing the real repo), and `test_a_removed_gate_verb_fails` proves the inverse. That is exactly the durable property `kbqpkn` shipped the file for.

    **BARE-SUITE BEFORE / AFTER DELTA, MEASURED IN THIS WORKTREE.** Both runs are bare `python3 -m pytest` (configured `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow'`).

    BEFORE (measured in this lane at base HEAD `22cf67d9`, before any edit):

    ```
    =========================== short test summary info ============================
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    FAILED tests/test_agy_runipd_cli.py::AgyCostAttributionTests::test_agy_does_not_import_the_record_builder_FROM_oc_runipd
    FAILED tests/test_oc_runipd.py::AgyCardIsNotResolvableTests::test_the_shared_symbol_lives_in_runner_shared_NOT_in_oc_runipd
    3 failed, 9097 passed, 3 skipped, 2 xfailed, 6 warnings in 327.05s (0:05:27)
    ```

    AFTER (same command, after this turn's plan/backlog writes):

    ```
    =========================== short test summary info ============================
    FAILED tests/test_oc_runipd.py::AgyCardIsNotResolvableTests::test_the_shared_symbol_lives_in_runner_shared_NOT_in_oc_runipd
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    FAILED tests/test_agy_runipd_cli.py::AgyCostAttributionTests::test_agy_does_not_import_the_record_builder_FROM_oc_runipd
    3 failed, 9097 passed, 3 skipped, 2 xfailed, 6 warnings in 150.33s (0:02:30)
    ```

    FAILING NODE ID SETS, compared as SETS because the printed order varies with `-p randomly`'s seed and `-n auto` sharding:

    * BEFORE = {`test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, `test_agy_runipd_cli.py::AgyCostAttributionTests::test_agy_does_not_import_the_record_builder_FROM_oc_runipd`, `test_oc_runipd.py::AgyCardIsNotResolvableTests::test_the_shared_symbol_lives_in_runner_shared_NOT_in_oc_runipd`}
    * AFTER = the same three node ids.
    * **AFTER minus BEFORE = EMPTY.** (BEFORE minus AFTER is also empty; passed/skipped/xfailed counts are identical at 9097/3/2.)

    THE THREE FAILURES ARE PRE-EXISTING AND OUTSIDE THIS PLAN'S REACH, which matters because the plan warned against reusing any figure from this Set. Note this baseline DIFFERS from the review-measured F-14 figure (`1 failed, 7942 passed`): there are now THREE failures and 9097 passing tests, so measuring my own was necessary rather than a formality, exactly as the validation section required. (1) `test_turn_bounds` is the environmental one F-14 identified: it asserts `'OPENCODE_CONFIG_CONTENT' not in main_env` and that variable is exported into this agent session, filed by `y9vpvv` as backlog `cfgj8s`. (2) and (3) are a RUNNER-MODULE-LAYOUT pair asserting where shared symbols live (`assertEqual(len(from_oc), 56)` observing 4), concerning `oc_runipd`/`agy_runipd`/`runner_shared` re-homing; they reproduce standalone at base HEAD in 0.51s with no edit of mine involved, and nothing this turn touched those modules (this turn's only writes are one plan file and one backlog file).

    **`pre-commit run --all-files`, ALL TEN HOOKS PASS:**

    ```
    $ pre-commit run --all-files
    trim trailing whitespace.................................................Passed
    fix end of files.........................................................Passed
    check yaml...............................................................Passed
    check for added large files..............................................Passed
    Detect hardcoded secrets.................................................Passed
    ruff.....................................................................Passed
    ruff-format..............................................................Passed
    no local leaks in tracked files..........................................Passed
    no raw plan->executed commit (use aw ipd finalize).......................Passed
    no untooled plan status change (use aw set)..............................Passed
    ```

    `ruff-format` PASSED, so F-09's correction holds and no failure needed treating as mine. Judged by RUNNING THE HOOK, never by ambient `ruff` (the ambient binary is a different version from the pinned `rev: v0.4.4` at `.pre-commit-config.yaml:43` and would report spurious reformatting).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: go-pending-approval`, WRITTEN BY `/plan-review` ON 2026-09-21 as that workflow's attested output. It was correctly ABSENT while the plan was unreviewed, because hand-writing it would have forged a review that never happened. `go-pending-approval` means the plan passed review and awaits sign-off; it is NOT an approval. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`.

THIS PLAN RUNS LAST IN ITS SET, BY CONSTRUCTION. It declares `Item-Dependencies: executed:kbqpkn, executed:y9vpvv` because a comparison of two children's shipped output cannot run before both have shipped. `kbqpkn` is already `executed`; `y9vpvv` is `approved` with its own `executed:lqly9m` edge now SATISFIED (`lqly9m` is `executed`), so the remaining sequencing is `y9vpvv` then this plan. Under a runner, `dependency_depth` sorts this item last in the Set and the edge is re-checked AT DISPATCH, so if `y9vpvv` has not landed this item is marked `dependency-blocked` and the run continues rather than failing. That is correct behavior and is not a defect to report.

WHAT THIS PLAN DOES TO ITS PARENT, stated so nobody mistakes the intent: NOTHING is deleted from `ao1rb7`. Its E-01, E-02 and E-03 stay exactly as authored, because that checklist is what makes `execute commitguard` complete when a human drives the Set with no runner involved. This plan's row is ADDED to the parent's `## Child IPDs` table so the parent's Set is covered, which is what lets the ORCHESTRATOR COVERAGE GATE pass and lets the runner retire the parent honestly once every child is `executed`. The parent's E-03 is then discharged by CITING this child's pasted evidence, which is the correct discharge for an orchestration item.

Execution contract: commit ONLY files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED CHECKOUT with other agents and humans working concurrently: verify the staged set with `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on rejection and can leave paths you never staged in the index. Do NOT reach for `--no-verify` anywhere in this Set: the Set's whole subject is the honesty of local guards, so bypassing one to land a change about them would be self-refuting. Do not delete or stage another party's untracked files (notably any `opencode-recovery/` dump), even to make a suite green.

SCOPE FENCE, AS A DECLARATION RATHER THAN A STOP CONDITION: the five `Scope-Paths` entries are declared so the runner can reconcile afterwards what was and was not touched. An out-of-scope edit is MADE AND THEN JUSTIFIED at finalize with `--scope-reason`, not a reason to halt. The EXPECTED case here is the opposite direction and it needs `--scope-ack` per untouched declared path (see E-03); neither is a defect. The one condition that genuinely warrants STOPPING and reporting is the one the spec-sync section already names: a shipped sentence that contradicts a `.spec.md` rather than the code, since amending a spec must be declared before the run starts.

WHEN YOU REPORT TESTS PASSED, PASTE THE ACTUAL RUNNER OUTPUT. Every `V-*` above demands pasted evidence, and a summary line you did not produce by running the command is a fabrication, not a shortcut. This plan's whole subject is prose that overclaims what a mechanism does, so claiming an unrun verification here would be the same defect it exists to find.

LIFECYCLE TRANSITION: when every `E-*` is performed and every `V-*` carries pasted evidence, this plan moves to `.aw/records/plans/executed/` through `aw ipd finalize` (with the `--scope-ack` flags E-03 names), NEVER by a hand-rolled `git mv`. IF A RUNNER IS DRIVING THIS PLAN, the runner owns `aw ipd begin` and `aw ipd finalize` and auto-reconciles the scope delta; do not invoke either yourself in that case. An agent or human executing this plan directly owns both calls.
