# IPD: Reject an unparseable actor at the setter instead of wedging finalize after the lifecycle commit

- Date: 2026-09-08
- Kind: child
- Concern: `ipd_lint._HISTORY_ATTRIB_RE` captures a history line's actor with `\((?P<actor>[^)]*)\)`, so `[^)]*` stops at the FIRST closing paren and an actor containing parens never matches at all. `_newest_executed_history` then falls through to its bare-line branch and returns `("", "")`, so IPD-S406 reports an EMPTY actor and an EMPTY summary for a line where both are plainly present. Because IPD-S406 runs as POST-TRANSITION validation, the lifecycle COMMIT already exists when it fires, and finalize lands in COMMITTED-INCOMPLETE telling the operator to "re-run the SAME command to resume" - which cannot succeed, because the offending text is now in the file and the regex still cannot parse it. The only way out is hand-editing a plan already in `executed/`, which trips the executed-transition gate too, so one bad character class costs two gate bypasses. THE SAME `[^)]*` BOUND IS COPIED INTO TWO MORE READERS AND ONE OF THEM IS A GATE THAT FAILS OPEN (found at review, F-12/F-13): `plan_readiness._HISTORY_RECORD_PARTS_RE` (`:343`) cannot recognize a parenthesized-actor line as a REVIEW record, so `newest_verdict` returns None, so `approval_refusals` emits ZERO refusals for a plan whose own newest review says `REJECT - NEEDS REPLAN` - the exact refusal the `apprvguard` gate exists to make unbypassable. Reproduced end to end. And `record_history._TAIL_RE` (`:293`) feeds `ipd_lifecycle._plan_status_events`, so `derive_plan_status` reads a parenthesized `executed` line as the PREVIOUS status. The wedged finalize is therefore the visible symptom of a defect whose worst instance is silent.
- Scope: Fail FAST at the setter so the committed-incomplete state cannot be reached: reject a parenthesized `--actor` in the finalize paths, mirroring the guard that ALREADY exists in `retire_orchestrator` but is missing from the finalize path that mutates. Also widen EVERY reader that carries the same `[^)]*` actor bound - the attribution lint, the approval gate's review-record discriminator, and the shared inline-history parser - since a setter guard cannot fix a line that is already on disk, and one of those readers is a gate that currently fails open. Reconcile the `Author` / `actor` spellings so the tooling stops teaching the shape the readers reject.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_authoring.py, agent_workflows/plan_readiness.py, agent_workflows/record_history.py, tests/test_ipd_lint.py, tests/test_ipd_lifecycle_cli.py, tests/test_orchestrator_retirement.py, tests/test_plan_readiness.py, tests/test_record_history.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: actorparen
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: fn2l1u
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: wwdm4g
- Blocks-Release: next

## Workflow history
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-09 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 1: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-501..PR-511, ALL ELEVEN FIXED, no open questions remain (both pre-existing OQs carry maintainer rulings and stay resolved). The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's FIRST verdict token. `aw ipd lint` CONFORMING at `--phase author` before semantic review and at `--phase review-finalize` after every revision; the one `IPD-Z602` advisory on E-07 was assessed semantically and deliberately not split (its second clause is the guard's own blast radius, not an independent deliverable). THE FINDING THAT RESHAPED THE PLAN IS THAT IT WAS FIXING THE VISIBLE HALF OF THE DEFECT (PR-501, new F-12). Grepping for the CHARACTER CLASS rather than the symptom found the identical `[^)]*` actor bound in two more readers, and one of them backs the APPROVAL GATE. Reproduced end to end through the real CLI in a scratch repo: with a parenthesized actor, `aw set reviewed <id6> -m "/plan-review: REJECT - NEEDS REPLAN"` then `aw set approved <id6> --by-human` EXITS 0 and writes `- Status: approved`; with the slash form the identical second command EXITS 1 and refuses with "This refusal has NO override." So a formatting accident silently converts the one un-overridable approval refusal into a no-op, which is precisely the failure `apprvguard` was built after. New E-07 closes it at `status_set.apply_status_change`, the SINGLE writer every `--actor` surface funnels into, and new E-08 widens the two other readers; `Scope-Paths` grew by `plan_readiness.py` and `record_history.py` plus their tests, and the gate now tells an executor who runs short to do E-01/E-07/E-08a and stop, because that ordering fixes the gate while E-03 alone fixes only a lint. THE PRESCRIBED IMPLEMENTATION WAS REVERSED ON MEASUREMENT (PR-503, F-14) and this is the finding a re-reviewer should check first: E-03 said to anchor the capture on the trailing `):`, which is GREEDY, and greedy CORRUPTS a line that parses correctly today (`(opencode/model): fixed foo(bar): baz` -> actor `opencode/model): fixed foo(bar`), which is the plan's own named hazard case. The LAZY capture handles all four fixtures and, over all 3163 tracked history records, changes 0 previously-parsing captures while newly parsing 336; V-03 now requires the greedy form's FAILURE to be exhibited so the choice is evidenced. PR-502 (F-13) found the third reader, `record_history._TAIL_RE`, whose breakage makes `derive_plan_status` report the PREVIOUS status for a parenthesized terminal line; fixing it moves `check_lifecycle_transitions` 15 -> 16 findings and THE NEW ONE IS A TRUE POSITIVE (a real backwards `to-review` -> `draft` in `rununify-00-5e4sb6`) that E-04 must surface and must not suppress. F-4's ENUMERATION WAS WRONG IN BOTH DIRECTIONS (PR-505): `finalize_precheck` takes no actor so it was never a hole, `finalize` ALREADY guards an empty actor at `:2448` and is the correct insertion point, and there are THREE callers of that choke point including `status_set._delegate_plan_executed_to_finalize`, which the plan never mentioned; every cited line number was stale by ~180 lines and all were re-measured at HEAD `95f0f816`. THE STATED BASELINE AND ITS NAMED KNOWN-FAILURE WERE BOTH FALSE (PR-504): the suite is `1 failed, 5929 passed, 3 skipped, 2 xfailed`, the single failure is the ENVIRONMENTAL `test_reporting_contract` parity case (a gitignored local `opencode-recovery/` dump), and the claimed `test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` DOES NOT EXIST anywhere in the suite while `test_orchestrator_retirement.py` is `112 passed` in isolation - so an executor could have excused breaking one of the three tests E-01 must preserve. Also fixed: scaffold WRITES the broken shape rather than merely teaching it (PR-507, F-15: `--author` is interpolated into the first history line too, so every plan scaffolded with a parenthesized author is born unparseable); the dead `oc_runipd.finalize_orchestrator` still passes `--actor "aw oc run (orchestrator rollup)"` and the new guard would refuse it (PR-506, F-18, 0 callers by AST scan); the shared helper needs a placement that avoids an import cycle since `ipd_lifecycle` already imports `status_set` (PR-508); grandfathering means 43 unparseable `executed` lines yield only 6 IPD-S406 findings, so the lint payoff is small and the gate fix is the value (PR-509, F-16); 150 of 478 unparseable records fail on a MULTI-WORD workflow token, out of reach of this fix and now deferred by name so the residue cannot read as a failed fix (PR-510); and E-04 now depends on E-08 as well as E-03, since two of its three consumers are E-08's (PR-511). Verified sound and unchanged: the central discovery (the guard exists and is being lifted, not invented), the primary cascade, the `key=value` convention on both drivers, `_GENERIC_ACTORS` still capturing and rejecting both generic strings under the widened pattern, the decision to fix the input rather than reorder the transaction, and the refusal to rewrite the existing corpus. Six self-resolved decisions (D-1..D-6) recorded in the typed review record, all reversible; no `Reversible: no` decision was taken.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wwdm4g`, inheriting its `Blocks-Release: next` gate. NOTHING IN THIS ITEM IS OBSOLETE and no pending or approved plan touches it: grepping the whole pending tree and the specs tree for `HISTORY_ATTRIB`, `actorparen`, and "parenthesized actor" returns nothing, and the regex's last change is `99760832`, the commit that introduced the attribution lint. VERIFIED AT HEAD `8b4e1570` by running it rather than reading it: `_HISTORY_ATTRIB_RE` does NOT match `- 2026-08-30 executed (opencode (its_direct/pt3-claude-opus-5-1m-us)): did the work`, DOES match the slash form and returns `actor='opencode/its_direct/pt3-claude-opus-5-1m-us'`, and the full cascade reproduces: the bare-line pattern `_HISTORY_LINE_RE` DOES match the parenthesized line and yields group(1) `'executed'`, which is exactly the fallthrough that makes `_newest_executed_history` return `("", "")` and IPD-S406 (`C_EXEC_ATTRIBUTION`) report an empty actor. ONE MATERIAL DISCOVERY THAT RESHAPES THE PLAN, and it is the reason this is a narrowing-and-widening rather than a transcription: THE SETTER GUARD THE ITEM ASKS FOR ALREADY EXISTS, BUT IN EXACTLY ONE PLACE THAT IS NOT THE PATH THAT WEDGED. `retire_orchestrator` (`ipd_lifecycle.py:2008`) refuses a parenthesized actor BEFORE mutating anything (`:2079-2091`), with a comment that diagnoses this precise defect and names `oc_runipd.driver_actor` as the `key=value` precedent. I enumerated every finalize entry point and NONE of them carries that guard: `finalize_precheck` (`:1317-1477`), `finalize` (`:2241-2380`), `_finalize_transaction` (`:2380-2609`), `run_finalize` (`:2929-3054`) - all four report `paren-guard: False`. So the fix is to LIFT AN EXISTING, ALREADY-REVIEWED GUARD to the paths that need it, not to invent one. SECOND MEASUREMENT, which justifies keeping the item's option 1 alongside its option 2: 274 of 536 tracked plans carry a parenthesized `- Author:` (for example `Antigravity (Gemini 1.5 Pro)`, `assess-documentation workflow (agent)`), so the shape the tooling teaches is present in more than half the corpus. A setter guard prevents NEW wedges but cannot parse a line already written, which is why E-03 widens the regex too.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a formatting mistake in the actor string a refusal BEFORE anything is written, and make every reader of a history line able to parse the lines already on disk. Two harms, and the second was found at review and is the graver of the two. The FIRST is the one the backlog item reported: a post-commit formatting rule converts a typo into a wedged transaction whose own recovery instruction cannot work, and whose real recovery requires two `--no-verify` bypasses. The SECOND is silent: the same broken bound in `plan_readiness` makes the approval gate FAIL OPEN, so a plan whose newest review says `REJECT - NEEDS REPLAN` can be approved with exit 0 (F-12, reproduced end to end). A visible wedge costs an operator an hour; a gate that fails open costs the guarantee the gate exists to provide.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: refuse before anything is written (the item's option 2)

- [x] E-01 Lift the EXISTING parenthesized-actor refusal from `retire_orchestrator` (`agent_workflows/ipd_lifecycle.py:2258-2271`, re-measured at review; the plan previously cited `:2079-2091`, which is stale) into a single shared helper, and call it from the paths that mutate. Do NOT write a second copy of the check: the existing one is already reviewed, already carries the diagnostic message explaining the `\(([^)]*)\)` capture, and already points at the `key=value` remedy, so duplicating it would create two definitions of "valid actor" that can drift. Put the helper next to the other lifecycle validators and have `retire_orchestrator` call it too, so its behavior is byte-identical afterwards. Validate the actor BEFORE any journal write or file move: the whole point is that the refusal must precede the mutation. THE EXISTING BEHAVIOR IS PINNED BY A TEST that must keep passing UNMODIFIED: `tests/test_orchestrator_retirement.py:1653` (`test_a_parenthesized_actor_is_refused_BEFORE_any_mutation`) asserts `EXIT_CANNOT_RUN`, that the message contains `parenthesis`, that the plan file is untouched, and that HEAD did not move; its siblings at `:1622` (`test_the_actor_passes_the_attribution_lint`) and `:2042` (`test_an_empty_actor_is_refused`) constrain the same helper. NOTE ON PLACEMENT, since E-07 also needs this helper: `status_set` must be able to call it without importing `ipd_lifecycle` in a cycle. Verify the import direction before choosing the module (today `ipd_lifecycle` imports `status_set` as `_ss`, so the helper must NOT live in `ipd_lifecycle` if `status_set` is to call it); put it wherever both can reach and say why in a comment.
  - Depends on: none
  - Expected outcome: one shared actor validator, importable by both `ipd_lifecycle` and `status_set` with no import cycle; `retire_orchestrator`'s message and exit code are unchanged and its three existing actor tests pass unmodified; a parenthesized `--actor` is refused with a nonzero exit and NOTHING written.
  - Execution state: performed

- [x] E-02 Call the validator from the finalize CHOKE POINT, and do not repeat the plan's original enumeration, which was wrong in a way that would send the executor to the wrong function. RE-MEASURED AT REVIEW (HEAD `95f0f816`), correcting every coordinate and one substantive claim: `finalize_precheck` is `:1447-1653` and takes `(repo_root, plan_path)` ONLY - it never receives an actor, so it CANNOT guard one and must not be listed as a hole; `finalize` is `:2420-2556` and already validates a non-empty actor at `:2448` BEFORE any mutation, which is exactly where the paren check belongs; `_finalize_transaction` is `:2559-2786`; `run_finalize` is `:3114-3238` and reads the actor at `:3131`, then calls `finalize` at `:3210`. So `finalize` is the ONE function every caller reaches, and there are THREE callers, not two: `run_finalize` (the CLI), `retire_orchestrator`'s rollup path, and `status_set._delegate_plan_executed_to_finalize` (`status_set.py:1075`), which is the path `aw set executed` / `aw ipd set executed` take and which the plan never mentioned. Guard beside the existing empty-actor check in `finalize`; that single site covers all three. A second guard inside `_finalize_transaction` is optional defense-in-depth (both its callers are then guarded), so add it only with a comment saying it is redundant by construction. Note `_finalize_transaction` builds the history line by handing `actor` to `_ss.apply_status_change` via `argparse.Namespace(actor=actor, ...)` (`:2690`), which is the exact write this must precede.
  - Depends on: E-01
  - Expected outcome: a parenthesized actor is refused at `finalize` before any journal, status write, move, or commit; demonstrated separately through the CLI (`aw ipd finalize`) and through `aw set executed`, since those are two different callers of the same choke point.
  - Execution state: performed

- [x] E-07 CLOSE THE HOLE THAT ACTUALLY BREAKS A GATE: guard the actor in `status_set.apply_status_change`, the single writer of every artifact's history line (`agent_workflows/status_set.py:601` reads the actor, `:880` writes `- {today} {norm_status} ({actor}): {message}`). THIS IS THE MOST IMPORTANT ITEM IN THE PLAN and it was missing entirely; E-01/E-02 guard only the TERMINAL transition, but the damaging path is a NON-terminal one. REPRODUCED END TO END AT REVIEW in a scratch repo: `aw set reviewed <id6> --actor "opencode (its_direct/model)" -m "/plan-review: REJECT - NEEDS REPLAN"` writes the unparseable line, and the following `aw set approved <id6> --by-human` then EXITS 0 and sets `- Status: approved`. With the slash form the identical command EXITS 1 and refuses with "the newest review record states a verdict that does not clear this plan ... This refusal has NO override." So a parenthesized actor silently converts the ONE approval refusal that has no override into a no-op. That is the precise failure `apprvguard` was built after (a blanket approval sweeping five `REJECT - NEEDS REPLAN` plans into `approved`), and it is reachable today by any agent that copies its own parenthesized `- Author:` into `--actor`. Guard here, not only in the CLI parsers, because `apply_status_change` is what every `--actor` surface funnels into (`aw set`, `aw ipd set`, the finalize transaction, `specs.run_set`), so one guard covers them all and no new spelling can bypass it. Refuse with the SAME shared validator and the same message as E-01. Check the blast radius first: exactly ONE test in the suite passes a parenthesized actor (`tests/test_orchestrator_retirement.py:1666`) and it ASSERTS a refusal, so a refusal here is expected to break nothing. HANDLE THE ONE LIVE STRING F-18 FOUND: `oc_runipd.finalize_orchestrator` (`:836-859`) passes `--actor "aw oc run (orchestrator rollup)"` and would now be refused. It is DEAD (0 in-module calls, AST-verified; the live rollup path is `runner_shared.py:3319` -> `retire_orchestrator` with `driver_actor`), so the choice is between deleting the dead function and fixing its string to the `key=value` shape. Do ONE of the two deliberately and say which in a comment; leaving a call site that the new guard would refuse is not acceptable even when unreachable. Note `tests/test_lane_tool_identity.py:589-607` asserts `agy` deliberately has NO twin of this function, so do not add one.
  - Depends on: E-01
  - Expected outcome: `aw set <status> <plan> --actor "x (y)"` is refused with a nonzero exit and NO file written; the reproduced approve-over-a-rejection sequence above can no longer be created; the slash form is unaffected; no surviving call site in the package passes a parenthesized actor.
  - Execution state: performed

### Task group 2: make the already-written corpus parse in EVERY reader (the item's option 1)

- [x] E-03 Widen `_HISTORY_ATTRIB_RE` (`agent_workflows/ipd_lint.py:179-181`) so a parenthesized actor PARSES, because a setter guard cannot repair a line already on disk: measured at review, 43 `executed` history lines across the tracked plans corpus cannot be parsed by this pattern today, and 274 of 607 tracked plans carry the parenthesized shape in the `- Author:` field agents copy into `--actor`. Today the pattern is `^-\s+(?:\d{4}-\d{2}-\d{2})\s+(?P<status>\S+)\s+\((?P<actor>[^)]*)\)\s*:\s*(?P<msg>.*)$`. USE A LAZY CAPTURE `(?P<actor>.*?)`, NOT A GREEDY ONE, and this is settled by measurement rather than taste: the item's own suggestion of anchoring greedily on the trailing `):` was TESTED at review and is WRONG. Against `- 2026-09-08 executed (opencode/model): fixed foo(bar): baz` the greedy form captures actor `opencode/model): fixed foo(bar` and message `baz`, silently corrupting a line that parses CORRECTLY today; the lazy form yields actor `opencode/model` and message `fixed foo(bar): baz`, matching today's output exactly. Lazy also parses the parenthesized actor (`opencode (its_direct/model)`) and the both-hazards line (`(opencode (model)): fixed foo(bar): baz` -> actor `opencode (model)`, message intact). Do NOT loosen the date or status portions of the pattern while here.
  - Depends on: none
  - Expected outcome: the parenthesized actor line from the item's sighting 1 parses with the full actor and full message; the slash form parses byte-identically to today; a message containing `):` is not truncated and does not shift the actor boundary; the greedy alternative is demonstrated to FAIL that case, so the choice of lazy is evidenced rather than asserted.
  - Execution state: performed

- [x] E-08 Widen the SAME `[^)]*` bound in the two OTHER readers that carry it, because fixing only the lint leaves the failing-open gate in place. Both were found at review by grepping for the bound rather than by reading the plan's list. (a) `plan_readiness._HISTORY_RECORD_PARTS_RE` (`agent_workflows/plan_readiness.py:343`) - its `(?P<mid>[^(]*?)` and `(?P<actor>[^)]*)` together make `is_review_history_entry` return False for a parenthesized-actor review line, which is what zeroes out the approval refusal in E-07's reproduction. The lazy form `(?P<mid>.*?)\s*\((?P<actor>.*?)\):` was measured at review over all 3163 tracked history records: it changes the captures of ZERO previously-parsing lines and newly parses 336, so it is strictly additive. (b) `record_history._TAIL_RE` (`agent_workflows/record_history.py:293`) - same measurement, zero changed captures and 329 newly parsing. This one feeds `ipd_lifecycle._plan_status_events`, so today `derive_plan_status` on a plan whose newest line is a parenthesized `executed` returns the PREVIOUS status (measured: `approved` instead of `executed`). MIND THE ANTI-FORK RULE: `tests/test_plan_readiness.py:528` asserts there is only ONE encoding of the review vocabulary, so widen these patterns in place rather than adding a third.
  - Depends on: E-03
  - Expected outcome: a parenthesized-actor review line is recognized as a review record and its verdict is read; `derive_plan_status` returns `executed` for a parenthesized terminal line; both patterns are shown to leave every previously-parsing line's captures byte-identical.
  - Execution state: performed

- [x] E-04 Verify the WHOLE TRACKED CORPUS still behaves the same after E-03 and E-08, because widening a regex that feeds repository-wide rules can silently change findings on 607 files. Run BEFORE/AFTER and diff the finding sets for THREE consumers, not one, since E-08 adds two: (1) the IPD-S406 attribution rule across every tracked plan; (2) `check_engine.check_lifecycle_transitions`, which consumes `_TAIL_RE` through `_plan_status_events`; (3) `plan_readiness.newest_verdict` / `approval_refusals` across every tracked plan. Two outcomes are acceptable and must be distinguished: findings that DISAPPEAR because a real actor now parses, and findings that APPEAR. THE REVIEW ALREADY MEASURED ALL THREE, so these are the numbers to reproduce and explain, not to discover: IPD-S406 goes 6 findings -> 0 (three plans, each raising both the empty-actor and empty-summary diagnostic; all three are legitimately attributed and were false positives); `check_lifecycle_transitions` goes 15 -> 16, and THE ONE NEW FINDING IS A TRUE POSITIVE THAT MUST NOT BE SUPPRESSED (`rununify-00-5e4sb6` records a real backwards `to-review` -> `draft` transition that the broken parser was hiding); `newest_verdict` polarity changes on 45 of 607 plans, 44 None->positive and 1 None->neutral, with zero positive->negative or negative->positive flips, and 7 plans (all in `superseded/`) read `negative` under the fix. Pay specific attention to `_GENERIC_ACTORS` (`ipd_lint.py:184`): measured, `aw set` and `aw set, --by-human` are still captured exactly and still rejected. If the executor's own numbers differ from these, INVESTIGATE rather than adjusting the expectation: the corpus moves, so compare the CLASSIFICATION (no unexplained new finding, no lost true positive) and not the totals.
  - Depends on: E-03, E-08
  - Expected outcome: a before/after finding-set diff for all three consumers, with every change classified as an intended false-positive removal, a newly-visible TRUE positive (kept, not suppressed), or a regression (fixed); the `_GENERIC_ACTORS` rejection demonstrated still working.
  - Execution state: performed

### Task group 3: stop the tooling teaching the broken shape

- [x] E-05 Reconcile `Author` and `actor` so the two surfaces stop disagreeing silently (the item's option 4). `aw ipd scaffold --author` accepts and preserves a parenthesized string, and 274 of 607 tracked plans carry one, so an agent that copies its own `- Author:` into `--actor` produces a line the readers cannot parse; the divergence is only discovered AFTER a commit. NOTE THE SECOND SURFACE THE PLAN MISSED, verified at review: `--author` is written to TWO places, not one - the `- Author:` front-matter field (`ipd_authoring.py:184`) AND the scaffold's own first history line, `- {date} draft ({author}): created.` (`:40`, rendered at `:209`). Measured: `build_skeleton(author="opencode (its_direct/model)")` emits `- 2026-09-09 draft (opencode (its_direct/model)): created.`, which `record_history._parse_record_line` cannot parse today. So scaffold does not merely TEACH the broken shape, it WRITES one, and normalizing fixes both call sites at once. Decide ONE documented spelling and make the authoring surface emit it. RECOMMENDED, and cheap: NORMALIZE a parenthesized author to the parenthesis-free shape `driver_actor` already uses (`oc_runipd.py:862-883`, re-measured; its docstring states the rule and renders the model as `model=<model>`), so the form the tooling produces is the form the readers accept. Do NOT retroactively rewrite the 274 existing `- Author:` lines: they are not what breaks a gate (only the history-line actor is read), and E-03/E-08 make the parenthesized form parse anyway.
  RESOLVED BY THE MAINTAINER 2026-09-08 (OQ-02): NORMALIZE, AND SAY SO. Neither silent normalization (this plan's recommendation) nor refusal was taken. Emit ONE line telling the caller the author value was normalized, which answers the objection this plan itself recorded against silent rewriting: the string the user typed would otherwise not be the string recorded. Keep the notice to one line and do not style it as an error; this is a cosmetic field. A scaffold call that normalizes SILENTLY does not satisfy this item.
  - Depends on: E-01
  - Expected outcome: `aw ipd scaffold --author "X (Y)"` writes an author in the accepted shape AND prints one line saying it normalized the value; the choice is recorded in a comment; no existing plan file is rewritten.
  - Execution state: performed

- [x] E-06 Sweep for OTHER readers of the actor and CONFIRM the review's sweep rather than repeating it from scratch (the item's option 5). THE SWEEP WAS PERFORMED AT REVIEW and its result is E-08's existence, so this item's job is now to verify completeness and close the residue. The mechanical search that found them is `grep -n '\[\^)\]\*' agent_workflows/*.py`; re-run it and confirm the population, which was FIVE actor-bearing patterns: `ipd_lint._HISTORY_ATTRIB_RE` (`:180`, BROKEN, fixed by E-03), `plan_readiness._HISTORY_RECORD_PARTS_RE` (`:343`, BROKEN and gate-affecting, fixed by E-08a), `record_history._TAIL_RE` (`:293`, BROKEN, fixed by E-08b), `ipd_schema.py:1266` (`re.sub(r"\([^)]*\)", "", cleaned)` - NOT an actor reader; it strips parentheticals from E-item density text and must be left alone), and the three prose copies of the pattern inside comments/docstrings (`ipd_lifecycle.py:2139`/`:2259`/`:2268`, `oc_runipd.py:866`, `agy_runipd.py:900`), which are DOCUMENTATION that will become wrong once E-03 lands and MUST be updated in the same change. Then state a per-reader verdict against both spellings for the derived consumers, which have no pattern of their own but inherit these: `ipd_lint._newest_executed_history` (`:853-869`, the bare-line fallthrough returning `("", "")`), `_check_terminal_attribution` (`:872`), `plan_readiness.is_review_history_entry` / `newest_verdict` / `approval_refusals` / `is_plan_review_approved`, `record_history._parse_record_line` / `migrate_inline_history`, `ipd_lifecycle._plan_status_events` / `derive_plan_status`, and `check_engine.check_lifecycle_transitions` (`:1212`). Note two that are measured SAFE and must not be "fixed": `attention_contract.HISTORY_RECORD_RE` (`:537`) matches only the date prefix, and `plan_readiness.extract_newest_history_entry` / `history_verdict_approves` operate on the whole record text, so both handle either spelling (verified: `history_verdict_approves` correctly returns False for a parenthesized REJECT line).
  - Depends on: E-03, E-08
  - Expected outcome: the grep re-run and its population confirmed; a per-reader verdict table against both spellings; the three prose copies of the old pattern updated so no comment describes a bound the code no longer has; any additional broken reader either fixed here or recorded as a follow-up with its symbol named.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE GUARD ALREADY EXISTS, IN ONE PLACE ONLY. `retire_orchestrator` (`ipd_lifecycle.py:2187`) refuses a parenthesized actor at `:2258-2271`, before any mutation, with a message that explains the regex capture and names `oc_runipd.driver_actor` as the remedy. It is the model for E-01 and must not be duplicated. (Every coordinate in this section was re-measured at review against HEAD `95f0f816`; the plan's original line numbers were all stale by roughly 180 lines.)
- THE HISTORY LINE HAS EXACTLY ONE WRITER, and knowing that is what makes E-07 a one-site fix. `status_set.apply_status_change` (`:590`) reads `actor` at `:601`, folds in `--by-human` / `--allow-open-questions` suffixes at `:603`/`:613`, and writes `- {today} {norm_status} ({actor}): {message}` at `:880`. Every `--actor` surface funnels here: `aw set`, `aw ipd set`, `specs.run_set`, and the finalize transaction (`ipd_lifecycle.py:2690` hands it an `argparse.Namespace(actor=actor, ...)`).
- THE FINALIZE PATH HAS ONE CHOKE POINT AND THREE CALLERS. `finalize` (`:2420`) already refuses an empty actor at `:2448`; its callers are `run_finalize` (`:3210`), `retire_orchestrator` (`:2411`), and `status_set._delegate_plan_executed_to_finalize` (`status_set.py:1075`). `finalize_precheck` (`:1447`) takes no actor at all and therefore cannot be a hole.
- The `key=value`, parenthesis-free actor convention is established and documented in `driver_actor` (`oc_runipd.py:862-883`, and its twin `agy_runipd.py:896-903`), which renders the model as `model=<model>` and appends `variant=` and `profile=` the same way, explicitly so the attribution capture cannot misparse it.
- IPD-S406's constant is `C_EXEC_ATTRIBUTION`, and the rule reads ONLY the newest `executed` history entry. That bounds the LINT symptom to the terminal transition, but NOT the defect: the same broken bound in `plan_readiness` and `record_history` affects every status line, which is why the plan's scope grew at review.
- `_newest_executed_history` (`:853-869`) has a deliberate bare-line branch that returns `("", "")` so a bare `executed` line is FLAGGED rather than skipped. That design is correct; the bug is that a parenthesized line reaches it at all.
- `_GENERIC_ACTORS` (`:184`) is pinned NARROWLY on purpose (only the `aw set` defaults) with an explicit instruction not to expand it to bare tool or human names. E-04 must not disturb it.
- THE ANTI-FORK TESTS ARE REAL AND CONSTRAIN HOW E-08 IS WRITTEN. `tests/test_plan_readiness.py:528` asserts the retired private regexes are GONE rather than shadowed, and `:730` asserts the typed gate is called rather than reimplemented. Widen in place; do not add a parallel parser.
- THE ATTRIBUTION LINT IS GRANDFATHERED FOR PRE-CUTOFF PLANS (`_is_grandfathered_for_attribution`, keyed on `Scope-Paths` grandfathering), which is why only 6 IPD-S406 findings exist against 43 unparseable `executed` lines. The regex fix therefore has a much smaller lint-visible effect than the raw line count suggests, and the real payoff is the gate in E-07.
- The finalize transaction is two-phase with a journal and explicit phases, and post-transition validation runs AFTER the lifecycle commit by design (`PHASE_COMPLETE` at `:143`). That ordering is why a lint-class failure becomes a wedged transaction, and it is why this plan fixes the input rather than the ordering (see Deferred).
- The item's INTERIM GUIDANCE is verified and worth preserving in the refusal message: the slash form `opencode/its_direct/<model>` parses, and `z2isfg` was finalized with it cleanly.
- HISTORY IS NEWEST-FIRST (`status_set.py:870-880` PREPENDS under the heading). Any before/after corpus comparison in E-04 must take the FIRST record of the bounded section, via the shared `plan_readiness.extract_newest_history_entry`, and must not hand-roll another parser.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The regex genuinely cannot match a parenthesized actor: `[^)]*` stops at the first `)`. Measured, not read. | `ipd_lint.py:179-181`; measured `_HISTORY_ATTRIB_RE.match(...)` -> False for the parenthesized line, True for the slash form at `8b4e1570` |
| F-2 | The cascade to an EMPTY actor reproduces exactly as the item describes: the bare pattern matches the same line and yields group(1) `'executed'`, which is the fallthrough returning `("", "")`. | measured `_HISTORY_LINE_RE.match(...)` at `8b4e1570`; `ipd_lint.py:825-841` |
| F-3 | THE SETTER GUARD ALREADY EXISTS but only in `retire_orchestrator`, whose comment diagnoses this precise defect and names the `key=value` remedy. | `ipd_lifecycle.py:2187` (function), `:2258-2271` (the guard), re-measured at review |
| F-4 | CORRECTED AT REVIEW. The plan claimed four unguarded finalize paths; measured, `finalize_precheck` (`:1447-1653`) never receives an actor so it cannot guard one, and `finalize` (`:2420-2556`) ALREADY validates a non-empty actor at `:2448`, which is the correct insertion point. There is ONE choke point with THREE callers, one of which (`status_set._delegate_plan_executed_to_finalize`) the plan never mentioned. | measured at `95f0f816`: `finalize` signature + `:2448`; callers at `:3210`, `:2411`, `status_set.py:1075` |
| F-5 | The unguarded actor reaches the history writer directly: `_finalize_transaction` passes it to `apply_status_change` through `argparse.Namespace(actor=actor, ...)`. | `ipd_lifecycle.py:2690` |
| F-6 | The CLI reads the actor with no validation. | `ipd_lifecycle.py:3131` |
| F-7 | THE TRAP IS SYSTEMIC, which is why the readers must widen and not only the setter guard: 274 of 607 tracked plans carry a parenthesized `- Author:` (e.g. `Antigravity (Gemini 1.5 Pro)`), and 43 `executed` history lines in the corpus are unparseable by the attribution regex today. | measured at `95f0f816`; the plan's original denominator (536) was the count at `8b4e1570` |
| F-8 | NOTHING covers this item: no pending or approved plan and no spec mentions `HISTORY_ATTRIB`, `actorparen`, or a parenthesized actor. | grep over `.aw/records/plans/pending/` and `.aw/records/specs/` at `8b4e1570` |
| F-9 | The regex has not changed since the attribution lint was introduced, so the defect has been live for its whole life. | `git log -S` on the pattern -> single commit `99760832` |
| F-10 | The parenthesis-free convention is already documented and implemented on the runner side, so E-05's normalization has a precedent to copy rather than a new convention to invent. | `oc_runipd.py:853-874` |
| F-11 | The failure was observed TWICE by two different agents on the same day, one of whose in-flight fix was never committed and would have been reintroduced by merging its lane. That is what makes it a shape the tooling invites rather than one agent's typo. | backlog `wwdm4g`, "THE TWO SIGHTINGS" |
| F-12 | **THE SAME DEFECT SILENTLY DISABLES THE APPROVAL GATE, AND THAT IS WORSE THAN THE WEDGED FINALIZE.** `plan_readiness._HISTORY_RECORD_PARTS_RE` carries the identical `[^)]*` bound, so a parenthesized-actor review line is not recognized as a review record, `newest_verdict` returns None, and `approval_refusals` returns ZERO refusals for a plan whose newest review says `REJECT - NEEDS REPLAN`. Reproduced END TO END in a scratch repo: with the parenthesized actor `aw set approved <id6> --by-human` exits 0 and writes `- Status: approved`; with the slash form the identical command exits 1 and refuses with "This refusal has NO override." | `plan_readiness.py:343`; reproduction via `aw set reviewed`/`aw set approved` at `95f0f816`; the gate's rationale at `plan_readiness.py:330-338` |
| F-13 | A THIRD reader carries the same bound: `record_history._TAIL_RE` feeds `ipd_lifecycle._plan_status_events`, so `derive_plan_status` on a plan whose newest line is a parenthesized `executed` returns the PREVIOUS status (measured: `approved`, not `executed`). `check_engine.check_lifecycle_transitions` consumes the same events, and fixing the bound makes ONE real backwards transition visible that was hidden (15 -> 16 findings, the new one a TRUE positive in `rununify-00-5e4sb6`). | `record_history.py:293`; `ipd_lifecycle.py:768`; `check_engine.py:1212`; measured before/after at `95f0f816` |
| F-14 | THE GREEDY FIX THE BACKLOG ITEM SUGGESTED IS WRONG, measured rather than reasoned. Anchoring greedily on the trailing `):` corrupts a line that parses correctly TODAY: `- 2026-09-08 executed (opencode/model): fixed foo(bar): baz` yields actor `opencode/model): fixed foo(bar`. The LAZY capture `(?P<actor>.*?)` handles all four cases correctly and, over all 3163 tracked history records, changes the captures of ZERO previously-parsing lines while newly parsing 336. | measured at `95f0f816` against the corpus; backlog `wwdm4g` option 1 |
| F-15 | `aw ipd scaffold --author` does not merely TEACH the broken shape, it WRITES one: the author string is emitted into the front matter AND into a `- {date} draft ({author}): created.` history line, which `record_history._parse_record_line` cannot parse when the author is parenthesized. | `ipd_authoring.py:40` (template), `:184` (front matter), `:209` (render); measured via `build_skeleton` |
| F-16 | The attribution lint is GRANDFATHERED for pre-cutoff plans, which is why 43 unparseable `executed` lines produce only 6 IPD-S406 findings. The lint-visible payoff of E-03 is therefore small; the gate fix in E-07 and the reader fixes in E-08 are where the value is. | `ipd_lint._is_grandfathered_for_attribution` (`:838-850`); measured 6 findings across 3 plans |
| F-17 | Exactly ONE test in the whole suite passes a parenthesized `--actor`, and it ASSERTS a refusal. So adding the refusal at the shared writer has a measured blast radius of zero. | `grep -rn 'actor="[^"]*(' tests/*.py` -> `tests/test_orchestrator_retirement.py:1666` only |
| F-18 | ONE LIVE STRING IN THE PACKAGE STILL PASSES A PARENTHESIZED ACTOR, and it is the exact string this defect was first diagnosed from: `oc_runipd.finalize_orchestrator` passes `--actor "aw oc run (orchestrator rollup)"`. It is DEAD CODE (0 in-module calls, verified by AST; the live path is `runner_shared` -> `_lifecycle.retire_orchestrator`, which uses `driver_actor` and already refuses parens), so E-07's guard cannot break a live runner. It must still be handled deliberately rather than left as a loaded gun. | `oc_runipd.py:836-859` (the function), `:848` (the string); AST scan for calls -> 0; live path `runner_shared.py:3319` |

## Proposed changes (ordered, validatable)

1. Extract the existing parenthesized-actor refusal into one shared validator, importable without an import cycle (E-01).
2. Call it from the `finalize` choke point, covering all three of its callers (E-02).
3. Guard the SHARED history writer `status_set.apply_status_change`, which is what closes the failing-open approval gate (E-07). This is the highest-value item.
4. Widen the attribution regex with a LAZY capture, proven against the greedy alternative (E-03).
5. Widen the same bound in `plan_readiness` and `record_history`, the two other readers carrying it (E-08).
6. Diff the findings of all THREE affected consumers across the tracked corpus before and after, keeping the newly-visible true positive (E-04).
7. Make `scaffold` emit an author in the accepted shape, in BOTH places it writes one, and say it normalized (E-05).
8. Confirm the reader sweep, update the three prose copies of the old pattern, and report a per-reader verdict (E-06).

## Deferred / out of scope (with reason)

- MOVING IPD-S406 TO RUN BEFORE THE LIFECYCLE COMMIT (the item's option 3). This is the deepest framing and the item is right that a post-commit formatting rule is the underlying design smell, but reordering the two-phase finalize transaction is a change to the transaction's own contract, with rollback and journal-phase consequences, and it would not be validated by anything this plan tests. Fixing the INPUT (E-01/E-02) removes the reachable path to the wedge; reordering the gate is a separate, larger design item.
- REWRITING THE 274 EXISTING PARENTHESIZED `- Author:` LINES. They are not the defect: only the history-line actor is read by a gate, and E-03/E-08 make the parenthesized form parse regardless. A 274-file rewrite would be pure churn with a real chance of collateral damage.
- REWRITING THE 328 ALREADY-WRITTEN PARENTHESIZED HISTORY LINES. Same reasoning, and now measured: widening the readers (E-03/E-08) makes all of them parse without touching a single tracked file, so a rewrite would buy nothing and would edit plans in `executed/`, which is itself gated.
- WIDENING THE 150 HISTORY LINES WHOSE MIDDLE IS MULTI-WORD rather than parenthesized (e.g. `- 2026-07-26 fleshed to a design spec from research (actor): msg`). Measured at review: of 478 records `record_history._TAIL_RE` cannot parse, 328 fail because of the parenthesized actor (fixed here) and 150 fail because the workflow token is multi-word, which `\S+` rejects. `plan_readiness._HISTORY_RECORD_PARTS_RE` already tolerates a multi-word middle, so this affects only the sidecar migration path and no gate. It is a genuinely separate defect: fixing it means deciding what the workflow token IS, which is a grammar change, not a bound widening. FILE IT rather than fold it in.
- THE ONE NEWLY-VISIBLE BACKWARDS TRANSITION in `rununify-00-5e4sb6` (`to-review` -> `draft`). E-04 must SURFACE it and must NOT suppress it; correcting that plan's own history is a separate act on a separate artifact, and doing it inside this plan would put an unrelated pending plan's file in this plan's commit.
- EXPANDING `_GENERIC_ACTORS`. Pinned narrowly on purpose with an explicit instruction not to widen it to bare tool or human names. E-04 only proves it still works.
- FIXING THE EXECUTED-TRANSITION GATE bypass this defect cascades into. That is backlog `gjadwm`, whose case 2 is graduated separately as plan `i4c0c3` in this same batch, and whose case 1 is owned by approved plan `29wvmj`. Once either lands, recovering from a wedge stops needing the second bypass; this plan removes the need for the FIRST one.
- THE SIBLING RECEIPT/JOURNAL DEFECTS the item groups with this one (`xmqv5l`, `v880xk`). Separate open items outside this plan's ownership. The item's argument that the finalize-evidence model deserves one coherent review is reasonable but is a different piece of work.

## Scope check

- Over-scope: `agent_workflows/ipd_authoring.py` is in `Scope-Paths` for E-05, which implements the item's option 4 rather than its core defect. It is included because the item identifies the `Author`/`actor` divergence as the REASON agents keep writing the broken form, and F-15 upgrades that from "teaches it" to "writes it", so cutting E-05 would leave a scaffold that emits an unparseable history line on every new plan. A reviewer may still cut it without affecting E-01/E-02/E-07/E-03/E-08.
- Scope GREW at review, deliberately, and this is the one thing a re-reviewer should scrutinize. `plan_readiness.py` and `record_history.py` (plus their two test files) were ADDED to `Scope-Paths` because F-12 and F-13 found the same defect there and one of them is a gate that fails open. The alternative was to ship a plan that fixes the LINT while leaving `aw set approved` bypassable by a formatting accident, which would have been a worse outcome than a wider plan. The growth is bounded: three regex bounds, one shared guard, and no new abstraction.
- Under-scope: the gate-ordering redesign, the 274-author-line rewrite, the 328-history-line rewrite, the 150 multi-word-middle records, and the cascading executed-gate bypass are all left alone (see Deferred).

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. THE BASELINE THE PLAN STATED IS WRONG AND ITS NAMED FAILURE DOES NOT EXIST; both were re-measured at review, and an executor inheriting the old text would have excused a real regression as a known one. Measured at HEAD `95f0f816`: `1 failed, 5929 passed, 3 skipped, 2 xfailed`. The single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, and it is ENVIRONMENTAL and MACHINE-SPECIFIC: it globs the whole tree and trips over a gitignored local `opencode-recovery/` dump (189 files), so it will not reproduce on a clean checkout. The plan's claimed known failure in `test_orchestrator_retirement.py` (`test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`) DOES NOT EXIST: no such test name is in the suite, and that module is `112 passed` in isolation. Measure YOUR OWN baseline before starting and compare NODE IDS, never totals.
- `python3 -m pytest tests/test_ipd_lint.py tests/test_ipd_lifecycle_cli.py tests/test_orchestrator_retirement.py tests/test_plan_readiness.py tests/test_record_history.py tests/test_event_derived_lifecycle.py` for the focused surface, widened at review to cover the two readers E-08 touches and the derivation E-08b affects. Measured green at review: `327 passed in 4.29s`.
- A REAL end-to-end refusal, for BOTH guards separately: (a) `aw ipd finalize` with a parenthesized `--actor` against a fixture plan, and (b) `aw set <status>` with a parenthesized `--actor`. Each must exit nonzero having created no journal, no move, no file write, and no commit (`git status --porcelain` and `git log -1` before and after).
- THE GATE REGRESSION TEST, which is this plan's most important single piece of evidence: reproduce the F-12 sequence in a scratch repo and show it now REFUSES. Write `reviewed` with a parenthesized actor and a `REJECT - NEEDS REPLAN` message, then attempt `aw set approved --by-human`. Before the fix that sequence exits 0 and writes `- Status: approved`; after it, either the write is refused at E-07 or the approval is refused at the gate. Both are acceptable outcomes; silently approving is not.
- The three-consumer finding-set diff from E-04 over all 607 tracked plans, with the newly-visible true positive kept.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`), since a piped `$?` reports the last pipeline stage.

## Spec / documentation sync

The IPD spec defines the `## Workflow history` line grammar `- <date> <status> (<actor>): <msg>` that this plan's regexes implement, so E-03/E-08 change only WHAT THE READERS ACCEPT, never the documented grammar: the parenthesized-actor line is already legal under that grammar and the readers were simply too strict. VERIFIED AT REVIEW that no spec text needs amending, by searching rather than assuming: `grep -rn '(<actor>)' .aw/records/specs/` returns nothing, no spec states a parenthesis rule for the actor, and the two IPD specs (`20260726-1340-01-ipd-spec`, `20260802-1904-01-ipd-structure-and-linting`) describe the history section without constraining the actor's characters. So no `.spec.md` file is edited and none is declared in `Scope-Paths`. ONE SPEC IS RELEVANT AND MUST NOT BE CONTRADICTED: `20260906-77tr3o-01` (`- Status: approved`) governs the rollup transition whose guard E-01 extracts; its R-4 constrains the terminal history MESSAGE and says nothing about the actor's characters, so refactoring the guard into a shared helper satisfies it unchanged, provided `retire_orchestrator`'s message and exit code stay byte-identical (which V-01 proves). IF the executor concludes the grammar itself must state a parenthesis rule, that IS a spec amendment: declare the spec path in `Scope-Paths` BEFORE editing it and say why here, per the plan-may-amend-a-spec rule.

THE REFUSAL MESSAGE IS OPERATOR-FACING DOCUMENTATION and must name the accepted shape (the slash form is verified to parse) rather than only rejecting the bad one. THREE IN-CODE PROSE COPIES OF THE OLD PATTERN BECOME WRONG the moment E-03 lands and are E-06's responsibility to correct: `ipd_lifecycle.py:2139`/`:2259`/`:2268`, `oc_runipd.py:866`, and `agy_runipd.py:900` all state the bound as `\(([^)]*)\)` and explain the refusal in terms of it. Leaving them would mean the code refuses a shape while its own comments explain the refusal with a rule that no longer exists. Note the refusal REMAINS correct after the widening, and the reason must be stated in those comments rather than assumed: the readers are now tolerant, but the parenthesis-free convention is still what every writer emits, so the guard enforces the CONVENTION rather than a parser limitation.

## Open questions

### OQ-01: Should the regex widen (E-03) as well as the setter refusing (E-01/E-02), or is the setter guard alone enough?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: CONFIRMED BY THE MAINTAINER 2026-09-08: DO BOTH, upholding the reviewer's resolution. The deciding evidence is that the two halves fix DIFFERENT populations and neither substitutes for the other: a setter guard prevents NEW wedges but cannot parse a line already on disk, and lines are already on disk (sighting 1 ended with a parenthesized line committed into an executed plan, and 274 of 607 plans carry the same shape in the field agents copy from - the figure was 536 when this was written and was re-measured at review), while a regex widening alone would make old lines readable but keep letting agents write the form the convention discourages. Doing both means new actors are clean AND old lines parse. The narrower alternative was put to the maintainer explicitly (cut E-03/E-04, lower risk, but leave every already-committed parenthesized terminal line permanently unparseable, fixable only by hand-editing a plan in `executed/` through two gates) and was rejected. E-03/E-04 stay. STRENGTHENED AT REVIEW: the ruling is now backed by a harder fact than the author had. The already-on-disk population is not merely inconvenient to read, it DISABLES A GATE (F-12), so "widen the readers" is no longer a convenience half of the fix.

### OQ-02: Should `scaffold` NORMALIZE a parenthesized `--author` or REFUSE it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: NORMALIZE, BUT SAY SO. Neither of the two options originally offered was taken. Silent normalization was recommended by this plan on the grounds that `--author` is a cosmetic front-matter field that breaks nothing alone, so refusing would fail a harmless call; refusing was the fail-fast-consistent alternative. The maintainer took the third option offered at decision time, which answers the exact objection this plan recorded against its own recommendation: silent normalization means "the author string a user typed is not the one recorded, which is a small surprise of its own". Printing one line that the value was normalized removes the surprise without refusing a harmless call. SO E-05 MUST EMIT A NOTICE, not merely normalize: a scaffold call that quietly rewrites the author is not sufficient. Keep it to one line; this is a cosmetic field and the notice should not read as an error.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new shared validator's source, and paste `git diff` of `retire_orchestrator` showing it now CALLS the helper. Prove `retire_orchestrator`'s behavior is unchanged by pasting its refusal message and exit code before and after (they must be identical strings), which is also what keeps approved spec `77tr3o` R-4 satisfied. Paste a grep proving there is exactly ONE definition of the paren check in the package. Paste proof there is no import cycle: `python3 -c "import agent_workflows.status_set, agent_workflows.ipd_lifecycle"` exits 0, and name the module the helper lives in with the reason.
  - Observed evidence: THE HELPER LIVES IN `agent_workflows/attention_contract.py:576` (`actor_refusal`) plus `ACTOR_PARENTHESIS_REMEDY` at `:570`. REASON, recorded as decision D1 and in a comment above the helper: `ipd_lifecycle` already imports `status_set` (lazily, as `_ss`, at `:2228`/`:2445`/`:2579`), so a helper hosted in `ipd_lifecycle` and called from `status_set` would close a cycle; `attention_contract` imports NOTHING from the package (AST check of module-level imports returned `[]`), already OWNS the history-record grammar (`HISTORY_RECORD_RE:537`) that the actor is a field OF, and is already imported by every caller. Source:
    ```python
    def actor_refusal(actor: Optional[str]) -> Optional[str]:
        if actor is None or not actor.strip():
            return "a non-empty actor is required."
        stripped = actor.strip()
        if "(" in stripped or ")" in stripped:
            return (
                f"actor {stripped!r} contains a parenthesis. The history line is "
                "'- <date> <status> (<actor>): <msg>', and every writer in this toolkit emits a "
                f"parenthesis-free actor, so a nested parenthesis is ambiguous. {ACTOR_PARENTHESIS_REMEDY}"
            )
        return None
    ```
    `retire_orchestrator` NOW CALLS IT (its 15-line inline copy is gone):
    ```diff
    -    if "(" in actor or ")" in actor:
    -        # F-4: `ipd_lint._HISTORY_ATTRIB_RE` captures the actor as `\(([^)]*)\)`, so a
    -        ...
    -        return FinalizeResult(EXIT_CANNOT_RUN, None, f"actor {actor!r} contains a parenthesis. ...", evidence)
    +    from agent_workflows import attention_contract as _ac
    +
    +    _actor_problem = _ac.actor_refusal(actor)
    +    if _actor_problem is not None:
    +        return FinalizeResult(EXIT_CANNOT_RUN, None, _actor_problem, evidence)
    ```
    EXACTLY ONE DEFINITION, four call sites (`grep -rn 'def actor_refusal' agent_workflows/` and `actor_refusal(`):
    ```text
    agent_workflows/attention_contract.py:576:def actor_refusal(actor: Optional[str]) -> Optional[str]
    agent_workflows/ipd_lifecycle.py:2274:    _actor_problem = _ac.actor_refusal(actor)      # retire_orchestrator
    agent_workflows/ipd_lifecycle.py:2467:    _actor_problem = _ac.actor_refusal(actor)      # finalize (E-02)
    agent_workflows/status_set.py:610:        _actor_problem = _ac.actor_refusal(str(_passed_actor))   # pre-flight (E-07)
    agent_workflows/status_set.py:637:    _actor_problem = _ac.actor_refusal(actor)      # writer backstop (E-07)
    grep for any OTHER hand-rolled check ('"(" in actor'): only attention_contract.py:590, the helper itself
    ```
    BEHAVIOR OF `retire_orchestrator`, before/after, called directly on all three actors:
    ```text
    BEFORE  actor='aw oc run (orchestrator rollup)'  exit=2
    AFTER   actor='aw oc run (orchestrator rollup)'  exit=2      <- exit code IDENTICAL
    BEFORE/AFTER actor=''      exit=2  msg=orchestrator rollup retirement requires a non-empty --actor.   <- byte-identical
    BEFORE/AFTER actor='   '   exit=2  msg=orchestrator rollup retirement requires a non-empty --actor.   <- byte-identical
    ```
    The PAREN message TEXT did change (deliberately, and this is the one honest deviation): the old wording explained the refusal in terms of the `\(([^)]*)\)` bound, which E-03/E-08 REMOVED, so keeping it would have made the code refuse a shape while its own message described a rule no longer in the source. The new text states the surviving reason (one actor shape toolkit-wide) and still names `key=value` + `oc_runipd.driver_actor`. SPEC `77tr3o` R-4 IS SATISFIED UNCHANGED: R-4 (spec `:170-173`) constrains only what the terminal history MESSAGE must say (retired-as-rollup, run id, children, no E/V claim); it says nothing about the actor's characters, and `rollup_history_message` is untouched. The three pinned tests pass UNMODIFIED (`git diff --stat tests/` shows no change to `test_orchestrator_retirement.py`): `python3 -m pytest tests/test_orchestrator_retirement.py -k actor` -> `3 passed, 109 deselected`. NO IMPORT CYCLE: `python3 -c "import agent_workflows.status_set, agent_workflows.ipd_lifecycle"` -> `exit=0`; `python3 -c "import agent_workflows.attention_contract, agent_workflows.plan_readiness, agent_workflows.record_history"` -> `exit=0`. Also pinned by a new test, `test_no_import_cycle_between_the_writer_and_the_lifecycle`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the invocation with a parenthesized `--actor` through BOTH callers separately (`aw ipd finalize` and `aw set executed`), each with its UNPIPED exit code, the refusal text, AND proof nothing was written: `git status --porcelain` unchanged, `git log -1` unchanged, and no finalize journal present (`ls` the journal path). Two callers of one choke point are two separate demonstrations. ALSO paste the re-measured coordinates that correct F-4: show `finalize_precheck`'s signature (proving it takes no actor, so it was never a hole) and `finalize`'s existing empty-actor check at its current line, so the executor's insertion point is evidenced rather than inherited from a stale citation.
  - Observed evidence: THE GUARD IS AT THE CHOKE POINT, beside the existing empty-actor check, covering all THREE callers from ONE site. Re-measured coordinates at this HEAD (correcting F-4 again; the review's own numbers had also drifted):
    ```text
    finalize_precheck signature: (repo_root: Path, plan_path: Path) -> Tuple[int, str, Dict[str, Any], Tuple[str, ...]]
      -> takes NO actor, so it never was a hole (F-4's original claim of four unguarded paths was wrong)
    finalize:2455  return FinalizeResult(EXIT_CANNOT_RUN, None, "finalize requires a non-empty --actor.")   <- pre-existing
    finalize:2467  _actor_problem = _ac.actor_refusal(actor)                                                 <- NEW (E-02)
    finalize:2469  return FinalizeResult(EXIT_CANNOT_RUN, None, f"finalize: {_actor_problem}")
    ```
    SCRATCH-REPO RUN, UNPIPED exit codes, with the plan-file digest / HEAD / `git status --porcelain` captured before and after each call (full transcript in the execution report):
    ```text
    (b) aw set executed <plan> --actor "opencode (its_direct/model)" -m done   UNPIPED exit=1
        refusal: FAIL Validation error on ...: actor 'opencode (its_direct/model)' contains a parenthesis.
                 The history line is '- <date> <status> (<actor>): <msg>', and every writer in this
                 toolkit emits a parenthesis-free actor ... Render qualifiers as key=value ...
        plan file digest unchanged: YES     HEAD unchanged: YES (a16e9b3c5af504aee028bc9468f073f27f340564)
        git status --porcelain unchanged: YES    finalize journal present: NONE    - Status: still `approved`
    (c) aw ipd set reviewed <plan> --actor "opencode (its_direct/model)"       UNPIPED exit=1   (same refusal, nothing written)
    (a) aw set reviewed  <plan> --actor "opencode (its_direct/model)"          UNPIPED exit=1   (same refusal, nothing written)
    CONTROL: aw set reviewed <plan> --actor opencode/its_direct/model          UNPIPED exit=0
             -> '- Status: reviewed' and '- 2026-09-14 reviewed (opencode/its_direct/model): review note'
    ```
    THE `aw ipd finalize` CLI SPELLING could not be demonstrated in THIS environment for an unrelated reason, and the honest detail matters: the lane runs with `AW_EXECUTION_ROLE=worker`, so `run_finalize` refuses at the worker-role gate (`AW-LIFECYCLE-ROLE-001`) BEFORE reaching the actor check - `UNPIPED exit=2`, nothing written. So the choke point was proven DIRECTLY instead, which is the stronger test because it shows the actor gate precedes even the file-exists check (i.e. before any possible mutation):
    ```text
    LC.finalize(Path("/nonexistent/repo"), Path("/nonexistent/repo/p.ipd.md"), actor, "msg", apply=True)
      actor='opencode (its_direct/model)'  exit=2  msg="finalize: actor '...' contains a parenthesis. ..."
      actor=''                            exit=2  msg='finalize requires a non-empty --actor.'
      actor='opencode/its_direct/model'   exit=2  msg='plan file not found: /nonexistent/repo/p.ipd.md'
                                                   ^ a VALID actor passes the gate and fails LATER
    ```
    Pinned by new tests in `tests/test_ipd_lifecycle_cli.py`: `test_aw_set_executed_refuses_before_the_finalize_transaction`, `test_finalize_refuses_the_actor_BEFORE_it_even_checks_the_plan_exists`, `test_finalize_precheck_takes_no_actor_so_it_never_was_a_hole`. All 10 tests in the new class pass.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: THE GATE REGRESSION, pasted in full, is this item's core. In a scratch repo, paste the BEFORE sequence exactly as the review measured it (write `reviewed` with a parenthesized actor and a `REJECT - NEEDS REPLAN` message; then `aw set approved --by-human` exits 0 and `- Status: approved` appears) and then the AFTER sequence showing it now refuses, with UNPIPED exit codes and the resulting `- Status:` line in both. Paste the guard's source at `apply_status_change`. Paste proof the refusal precedes the WRITE (the file is byte-identical after the refused call: `git status --porcelain` on it, or a digest before and after). Paste the grep from F-17 showing only one test passes a parenthesized actor and that it asserts a refusal. A demonstration through only `aw ipd set` does not satisfy this item, because the point is that every spelling funnels into one writer: show `aw set` too. Paste the disposition of F-18's dead call site (the deletion diff or the corrected actor string) plus the AST/grep proof it had no live caller.
  - Observed evidence: THE GATE REGRESSION, REPRODUCED AND THEN CLOSED, both runs through the real CLI in a throwaway git repo with the LANE's code pinned on `PYTHONPATH`. (Pinning matters and is itself a finding: the `aw` console script resolves `agent_workflows` relative to the process cwd, so the first attempt silently imported the MAIN CHECKOUT and reported the defect as unfixed. The harness now prints the resolved module path.)
    ```text
    BEFORE (git stash of my agent_workflows/ changes; identical fixture):
      --- PARENTHESIZED actor=<opencode (its_direct/model)>
          newest review record: - 2026-09-08 reviewed (opencode (its_direct/model)): /plan-review: REJECT - NEEDS REPLAN
          aw set approved --by-human   UNPIPED exit=0            <-- THE HOLE
          resulting status line: - Status: approved              <-- a REJECTED plan reached the execute-licensing state
          output: -    plan   20260908-repro-01-paren1  unchanged
      --- SLASH FORM    actor=<opencode/its_direct/model>
          aw set approved --by-human   UNPIPED exit=1
          resulting status line: - Status: reviewed
          output: FAIL Validation error ...: refusing to set approved for plan slash1: the newest review
                  record states a verdict that does not clear this plan, so approving it would license
                  execution of a plan its own review rejected. This refusal has NO override. ...

    AFTER (this change):
      --- PARENTHESIZED actor=<opencode (its_direct/model)>
          aw set approved --by-human   UNPIPED exit=1            <-- CLOSED
          resulting status line: - Status: reviewed
          output: FAIL Validation error ...: refusing to set approved for plan paren1: the newest review
                  record states a verdict that does not clear this plan ... This refusal has NO override.
                  Record: - 2026-09-08 reviewed (opencode (its_direct/model)): /plan-review: REJECT - NEEDS REPLAN.
      --- SLASH FORM: unchanged, UNPIPED exit=1, - Status: reviewed
    ```
    Note WHICH half closes it here: this AFTER run shows the E-08a READER fix refusing at the approval gate (the record was written before the guard existed, exactly the already-on-disk population a setter guard cannot help). E-07 independently stops such a record being WRITTEN at all - see the refusals in V-02. Both outcomes are acceptable per this item; silently approving is not, and it no longer happens by either route. THE GUARD'S SOURCE, at the single writer (`status_set.apply_status_change`, `:637`, before the `--by-human`/`--allow-open-questions` suffixes are folded in and before any file is touched):
    ```python
    actor = getattr(args, "actor", None) or "aw set"
    from agent_workflows import attention_contract as _ac

    _actor_problem = _ac.actor_refusal(actor)
    if _actor_problem is not None:
        raise ValueError(_actor_problem)
    ```
    and in the shared pre-flight (`validate_transition_allowed`, `:606-612`), which is what makes it a clean one-line CLI refusal for every record in a batch before any write:
    ```python
    _passed_actor = getattr(args, "actor", None)
    if _passed_actor is not None and str(_passed_actor).strip():
        from agent_workflows import attention_contract as _ac
        _actor_problem = _ac.actor_refusal(str(_passed_actor))
        if _actor_problem is not None:
            return False, _actor_problem
    ```
    Both, deliberately (decision D2): the pre-flight gives the clean refusal, the `raise` is the fail-closed backstop for a DIRECT caller that skipped it (e.g. `ipd_lifecycle._finalize_transaction`, which hand-builds an `argparse.Namespace`). An absent `--actor` is untouched, so the default `aw set` path never trips. THE REFUSAL PRECEDES THE WRITE, measured by digest, HEAD and porcelain around each refused call: `plan file digest unchanged: YES`, `HEAD unchanged: YES`, `git status --porcelain unchanged: YES`, `finalize journal present: NONE` (see V-02's transcript). EVERY SPELLING REFUSES, not just one: `aw set reviewed` (exit 1), `aw set executed` (exit 1), `aw ipd set reviewed` (exit 1), and the writer called directly raises `ValueError` (new test `test_the_writer_itself_raises_as_a_fail_closed_backstop`). F-17 CONFIRMED - only one test in the suite passes a parenthesized actor and it ASSERTS a refusal:
    ```text
    $ grep -rn 'actor="[^"]*(' tests/*.py
    tests/test_orchestrator_retirement.py:1666:            orch, "paren", apply=True, actor="aw oc run (orchestrator rollup)"
    (that is test_a_parenthesized_actor_is_refused_BEFORE_any_mutation, which asserts EXIT_CANNOT_RUN; it passes unmodified)
    ```
    F-18 DISPOSITION - the string was FIXED, not the function deleted (decision D3, with the reason: `tests/test_lane_tool_identity.py:585-609` cites this function as `oc`'s expected extra module-launch site and forbids an `agy` twin, so deleting it would erase a discussed design point and would require editing a test file outside `Scope-Paths`):
    ```diff
    -            "aw oc run (orchestrator rollup)",
    +            # Parenthesis-free `key=value`, the shape every writer in the toolkit emits (see
    +            # `driver_actor` below and `attention_contract.actor_refusal`).
    +            "aw oc run step=orchestrator-rollup",
    ```
    NO LIVE CALLER, verified by AST rather than grep (walking every `Call`/`Attribute`/`Name` node over `agent_workflows/*.py`, `tests/*.py`, `tools/**/*.py`): ZERO calls, ZERO attribute references, ZERO name references. Textual references are prose only (docstrings, plans, reviews, specs). The live rollup path is `runner_shared.py:3384` -> `ipd_lifecycle.retire_orchestrator` with `driver_actor` (already parenthesis-free). A new test, `test_no_call_site_in_the_package_passes_a_parenthesized_actor`, scans for `"--actor", "...("` literals and now reports none, so a future re-introduction fails the suite.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a snippet's output showing the widened pattern parsing all FOUR cases with their captured groups: the parenthesized actor from the item's sighting 1 (full actor, full message), the slash form (byte-identical to today's capture), the hazard case whose MESSAGE contains `):` (actor unchanged, message not truncated), and the both-hazards line. THEN paste the SAME four cases against the GREEDY alternative, showing it corrupts the third; a validation that does not exhibit the rejected alternative's failure has not proven the choice. Paste the old and new pattern side by side.
  - Observed evidence: THE TWO PATTERNS SIDE BY SIDE (only the actor capture changed; date and status untouched, as E-03 requires):
    ```text
    OLD  ^-\s+(?:\d{4}-\d{2}-\d{2})\s+(?P<status>\S+)\s+\((?P<actor>[^)]*)\)\s*:\s*(?P<msg>.*)$
    NEW  ^-\s+(?:\d{4}-\d{2}-\d{2})\s+(?P<status>\S+)\s+\((?P<actor>.*?)\)\s*:\s*(?P<msg>.*)$
                                                                    ^^^^ lazy, not [^)]* and not greedy
    ```
    ALL FOUR CASES against OLD / NEW(lazy) / the REJECTED greedy alternative, measured:
    ```text
    === OLD  (what shipped)
      paren  -> NO MATCH                                                          <-- the defect
      slash  -> actor='opencode/its_direct/pt3-claude-opus-5-1m-us' msg='did the work'
      hazard -> actor='opencode/model' msg='fixed foo(bar): baz'
      both   -> NO MATCH
    === LAZY (implemented)
      paren  -> actor='opencode (its_direct/pt3-claude-opus-5-1m-us)' msg='did the work'   <-- FULL actor, FULL message
      slash  -> actor='opencode/its_direct/pt3-claude-opus-5-1m-us' msg='did the work'     <-- byte-identical to OLD
      hazard -> actor='opencode/model' msg='fixed foo(bar): baz'                           <-- byte-identical to OLD
      both   -> actor='opencode (model)' msg='fixed foo(bar): baz'
    === GREEDY (the backlog item's suggestion; REJECTED)
      paren  -> actor='opencode (its_direct/pt3-claude-opus-5-1m-us)' msg='did the work'
      slash  -> actor='opencode/its_direct/pt3-claude-opus-5-1m-us' msg='did the work'
      hazard -> actor='opencode/model): fixed foo(bar' msg='baz'    <-- CORRUPTS a line that parses TODAY
      both   -> actor='opencode (model)): fixed foo(bar' msg='baz'  <-- also corrupt
    ```
    The four fixtures were, verbatim: `- 2026-08-30 executed (opencode (its_direct/pt3-claude-opus-5-1m-us)): did the work`, the same with the slash form, `- 2026-09-08 executed (opencode/model): fixed foo(bar): baz`, and `- 2026-09-08 executed (opencode (model)): fixed foo(bar): baz`. So F-14 is CONFIRMED by measurement rather than inherited: greedy is a regression on the hazard line, which is why the capture is lazy. END TO END through the real rule, not just the regex: `_newest_executed_history` on a plan whose newest terminal record carries a parenthesized actor now returns `('opencode (its_direct/some-model)', 'did the work and validated it.')` instead of `('', '')`, and `_check_terminal_attribution` returns 0 diagnostics. Pinned by 7 new tests in `tests/test_ipd_lint.py::ParenthesizedActorParsesInTheAttributionRegex`, INCLUDING `test_the_greedy_alternative_is_exhibited_as_WRONG`, which asserts the greedy form's corrupt capture so a later editor cannot "simplify" back to it. All 7 pass.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: for EACH of the two patterns separately, paste (a) the widened pattern, (b) a demonstration that a parenthesized line now parses with the correct captures, and (c) THE NO-REGRESSION PROOF, which must be corpus-wide rather than anecdotal: iterate every tracked history record and paste the count of previously-parsing lines whose captures CHANGED (must be 0) alongside the count newly parsing. Paste `is_review_history_entry` returning True and `newest_verdict` returning `negative` for a parenthesized REJECT line. Paste `derive_plan_status` returning `executed` for a parenthesized terminal line. Paste the anti-fork test file (`tests/test_plan_readiness.py`) passing, since it asserts there is only one encoding of this vocabulary.
  - Observed evidence: (a) THE TWO WIDENED PATTERNS. E-08a, `plan_readiness._HISTORY_RECORD_PARTS_RE` (`:361`) - note BOTH `mid` and `actor` became lazy, since `[^(]*?` on the middle also refused to cross an opening paren:
    ```text
    OLD  ^-\s*(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<mid>[^(]*?)\s*\((?P<actor>[^)]*)\):\s*(?P<msg>.*)$
    NEW  ^-\s*(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<mid>.*?)\s*\((?P<actor>.*?)\):\s*(?P<msg>.*)$
    ```
    E-08b, `record_history._TAIL_RE` (`:308`); the `workflow` token stays `\S+` deliberately (the multi-word middle is deferred by name):
    ```text
    OLD  ^(?P<workflow>\S+)\s*\((?P<actor>[^)]*)\):\s*(?P<message>.*)$
    NEW  ^(?P<workflow>\S+)\s*\((?P<actor>.*?)\):\s*(?P<message>.*)$
    ```
    (b) PARENTHESIZED LINES NOW PARSE WITH THE CORRECT CAPTURES:
    ```text
    E-08a on '- 2026-09-08 reviewed (opencode (its_direct/model)): /plan-review: REJECT - NEEDS REPLAN'
      mid='reviewed'  actor='opencode (its_direct/model)'  msg='/plan-review: REJECT - NEEDS REPLAN'
    E-08b on '- 2026-08-30 executed (opencode (its_direct/model)): did the work'
      workflow='executed'  actor='opencode (its_direct/model)'  message='did the work'
    ```
    (c) CORPUS-WIDE NO-REGRESSION PROOF over all 3073 tracked history records in 638 tracked plans, comparing the captures record-by-record BEFORE and AFTER:
    ```text
    pattern     previously-parsing records whose captures CHANGED   newly parsing   stopped parsing
    attrib      0                                                   355             0
    readiness   0                                                   362             0
    tail        0                                                   355             0
    ```
    Zero changed and zero lost in all three: the widenings are strictly ADDITIVE. (My newly-parsing counts are 355/362/355 against the review's 336/329; the corpus grew from 3163 to 3073 records across 638 rather than 607 plans between 2026-09-09 and today, so the totals moved in both directions. The property that matters - zero changed captures - is identical.) THE GATE-RELEVANT BEHAVIORS:
    ```text
    is_review_history_entry(paren REJECT record)     -> True      (was False)
    newest_verdict(paren REJECT plan)                -> 'negative' (was None)
    newest_verdict(slash REJECT plan)                -> 'negative' (unchanged: the SPELLING must not matter)
    approval_refusals(paren REJECT plan)             -> 1 refusal, containing 'NO override'  (was 0 refusals)
    derive_plan_status(paren terminal line)          -> 'executed' (was 'approved', i.e. lagging one transition)
    derive_plan_status(slash terminal line)          -> 'executed' (unchanged)
    ```
    THE ANTI-FORK CONSTRAINT IS RESPECTED: both patterns were widened IN PLACE, no third parser was added, and `tests/test_plan_readiness.py` (which asserts at `:528` that the retired private regexes are GONE rather than shadowed, and at `:730` that the typed gate is called rather than reimplemented) PASSES: `python3 -m pytest tests/test_plan_readiness.py` -> `74 passed`. 7 new tests in `AParenthesizedActorDoesNotDisableTheApprovalGate` cover the gate behavior, including `test_a_non_review_record_is_still_not_a_review_record`, which guards the d7bnhc F-5 hazard (a `to-review` record NARRATING a predecessor's rejection must still not be read as a verdict) - the widened `mid` capture could plausibly have broken that, and does not.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste BEFORE and AFTER counts plus the finding-set DIFF for all THREE consumers (IPD-S406 over tracked plans; `check_engine.check_lifecycle_transitions`; `plan_readiness.newest_verdict`/`approval_refusals`), with each change classified as an intended false-positive removal, a newly-visible TRUE positive, or a regression (and how it was fixed). THE NEW `check_lifecycle_transitions` FINDING MUST BE NAMED AND KEPT: paste it and state explicitly that it is a real backwards transition in another plan's history and was not suppressed. Paste a test showing `_GENERIC_ACTORS` still rejects `aw set` and `aw set, --by-human` under the new pattern. Compare your classification against the review's measured numbers (6->0, 15->16, 45 polarity changes all None->positive/neutral) and explain any divergence rather than restating it.
  - Observed evidence: Measured over all 638 tracked plans (`git ls-files .aw/records/plans`), BEFORE at HEAD `fea2c9f8` and AFTER with E-03 + E-08 both landed (E-04 depends on both, per the plan's ordering note).
    CONSUMER 1 - IPD-S406 attribution: **6 -> 0**, matching the review exactly. All six DISAPPEARED, all six were FALSE POSITIVES (each of three plans raised both the empty-actor and empty-summary diagnostic; all three are legitimately attributed, they simply carried a parenthesized actor):
    ```text
    DISAPPEARED  executed/20260829-promptmint-01-jxqdcw-...  IPD-S406 (nonempty summary + non-generic actor)
    DISAPPEARED  executed/20260829-runstop-04-foi1b3-...     IPD-S406 (both)
    DISAPPEARED  executed/20260829-wkindname-01-9trlc3-...   IPD-S406 (both)
    APPEARED     (none)
    ```
    CONSUMER 2 - `check_engine.check_lifecycle_transitions`: **11 -> 20**, i.e. NINE new findings across SIX plans, where the review measured 15 -> 16. DIVERGENCE EXPLAINED, NOT RESTATED, and I investigated rather than adjusting the expectation as E-04 instructs. FIVE of the six flagged plans are the `dirtygates` Set, first committed 2026-09-13, FOUR DAYS AFTER the review measured on 2026-09-09; they could not have been in its population, and the corpus also lost pending plans in between, which is why the BEFORE total differs too (11 vs 15). ALL NINE ARE TRUE POSITIVES AND ALL NINE ARE KEPT, verified individually by reconstructing each plan's oldest-first status stream (reading the file bottom-up, per the newest-first storage contract) and finding a genuinely backwards PAIR in every one:
    ```text
    pending/20260829-rununify-00-5e4sb6-...   'to-review'(08-30) -> 'draft'(08-29)      <- the one the review named
    pending/20260913-dirtygates-00-8lfoum-... 'reviewed' -> 'draft'
    pending/20260913-dirtygates-01-d7qoxv-... 'to-review' -> 'draft'  AND  'reviewed' -> 'to-review'
    pending/20260913-dirtygates-02-metc8b-... 'to-review' -> 'draft'  AND  'reviewed' -> 'to-review'
    pending/20260913-dirtygates-03-9iq461-... 'to-review' -> 'draft'  AND  'reviewed' -> 'to-review'
    pending/20260913-dirtygates-06-4xt6u4-... 'to-review' -> 'draft'
    ```
    NOT ARTIFACTS OF THIS CHANGE, proven by replaying the OLD `_TAIL_RE` over `rununify-00-5e4sb6`: the three offending records were UNPARSEABLE, i.e. INVISIBLE to the check, so the backwards pair could not be compared at all. The widening did not create the disorder, it revealed it.
    ```text
      2026-09-03 NEW token='approved'   | OLD parser: token='approved'
      2026-08-30 NEW token='reviewed'   | OLD parser: UNPARSEABLE (invisible to the check)
      2026-08-29 NEW token='draft'      | OLD parser: UNPARSEABLE (invisible to the check)
      2026-08-30 NEW token='to-review'  | OLD parser: UNPARSEABLE (invisible to the check)
    ```
    NOT SUPPRESSED AND NOT CORRECTED HERE, per this plan's own Deferred ruling: correcting another pending plan's history is a separate act on a separate artifact, and doing it here would put six unrelated plans' files in this plan's commit. Recorded as decision D4 with a follow-up flagged for their owners.
    CONSUMER 3 - `newest_verdict` / `approval_refusals`: **48 plans change polarity, all in the safe direction**; the review measured 45. Same corpus drift.
    ```text
    None->positive: 46      None->neutral: 2
    positive<->negative flips (must be 0): 0
    plans reading NEGATIVE after the fix: 7  (all 7 already read negative BEFORE; all 7 in superseded/)
    plans whose approval_refusals SET changed: 0
    ```
    Every change is a record that previously parsed as NOTHING now yielding a verdict; no plan's verdict reversed, and no plan GAINED a refusal (the seven negatives were already refusing). That the refusal set is unchanged corpus-wide while the synthetic REJECT fixture in V-07/V-08 flips from 0 refusals to 1 is consistent and worth stating: no tracked plan currently sits in the exact `reviewed` + parenthesized-REJECT state, so the corpus shows the fix as latent rather than active - which is precisely why the end-to-end reproduction in V-07 was required as separate evidence.
    A FOURTH CONSUMER MOVED THAT E-04 DID NOT LIST, and I am reporting it rather than burying it: `ipd_lifecycle.derive_plan_status` changed on 126 plans (123 `executed/`, 2 `pending/`, 1 `not-executed/`). Investigated as decision D5. For the 2 PENDING plans - the only lifecycle dir any consumer reads, since `check_lifecycle_transitions` skips non-pending explicitly at `:1204-1207` - the change is a CORRECTION: `specdispatch-01-mng63x` and `specsweep-01-ui8b9b` derived the stale `to-review` before and now derive `reviewed`, MATCHING their authoritative `- Status: reviewed`. The 123 terminal-dir differences trace to a PRE-EXISTING weakness independent of this plan: `_plan_status_events` `reverse()`s file order on a newest-first assumption that 36 of those files (stored oldest-first, pre-dating the convention) violate. No gate reads them, all four derivation tests pass, and fixing the ordering is a strictly larger behavior change than three regex bounds, so it is filed as a follow-up rather than folded in.
    `_GENERIC_ACTORS` STILL WORKS, untouched (E-04 must only prove it, not disturb it) - both strings are still captured EXACTLY and still recognized as generic under the new pattern:
    ```text
    '- 2026-08-30 executed (aw set): summary here'              -> actor='aw set'              in _GENERIC_ACTORS: True
    '- 2026-08-30 executed (aw set, --by-human): summary here'  -> actor='aw set, --by-human'  in _GENERIC_ACTORS: True
    ```
    pinned by the new test `test_the_generic_actor_rejection_still_works_under_the_new_pattern`, plus `test_the_attribution_lint_no_longer_reports_an_empty_actor` asserting a real parenthesized actor is NOT read as the generic default.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `aw ipd scaffold --author "opencode (its_direct/model)"` and BOTH resulting lines - the `- Author:` front-matter field AND the `- <date> draft (<author>): created.` history line - since F-15 shows the author reaches two places and normalizing only one leaves an unparseable history line in every new plan. Paste the one-line normalization notice the maintainer required (a silent rewrite does not satisfy OQ-02). Paste the resulting history line parsed by `record_history._parse_record_line` to prove it now parses. Paste the comment recording the OQ-02 choice. Paste proof no existing plan file was rewritten (`git status --porcelain` limited to `.aw/records/plans/`).
  - Observed evidence: THE REAL CLI, with a parenthesized `--author`:
    ```text
    $ python3 -m agent_workflows ipd scaffold --kind child --title "Demo plan" --set demo --order 1 \
        --author "opencode (its_direct/some-model)" --path <tmp>/20260914-demo-01-aaa111-demo-plan.ipd.md --apply
    note: normalized --author to 'opencode model=its_direct/some-model' (parentheses are not used in an
    actor/author; qualifiers are rendered key=value so history records stay parseable)
    wrote <tmp>/20260914-demo-01-aaa111-demo-plan.ipd.md
    ```
    BOTH WRITE SITES carry the normalized value (F-15's point: normalizing only the front matter would still leave every new plan born with an unparseable history record):
    ```text
    13:- Author: opencode model=its_direct/some-model
    18:- 2026-09-14 draft (opencode model=its_direct/some-model): created.
    ```
    THE NOTICE IS EXACTLY THE ONE THE MAINTAINER REQUIRED: one line, printed only when the value actually changed, and not styled as an error - `note: normalized --author to '...'`. A silent rewrite would not satisfy OQ-02, and two new tests pin this: `test_run_scaffold_PRINTS_that_it_normalized` (asserts exactly ONE such line and no `error`) and `test_no_notice_is_printed_when_nothing_changed`. THE RESULTING HISTORY LINE PARSES, through the reader that could not parse it before:
    ```text
    record_history._parse_record_line('- 2026-09-09 draft (opencode model=its_direct/some-model): created.')
      -> date='2026-09-09'  workflow='draft'  actor='opencode model=its_direct/some-model'  message='created.'
    ```
    and the shape scaffold now emits is the shape the setter ACCEPTS, which closes the loop the item is about: `attention_contract.actor_refusal('opencode model=its_direct/some-model')` -> `None` (accepted), while `actor_refusal('opencode (its_direct/some-model)')` -> a refusal. THE OQ-02 CHOICE IS RECORDED IN A COMMENT, at `ipd_authoring.run_scaffold`:
    ```python
    # OQ-02, as the maintainer ruled it: NORMALIZE the author, AND SAY SO. A silent rewrite would
    # mean the string the caller typed is not the string recorded, which is a small surprise of its
    # own; one line removes it without refusing an otherwise harmless call. Deliberately NOT styled
    # as an error (this is a cosmetic field), and printed only when the value actually changed.
    ```
    with the rule and its rationale also stated on `normalize_author`'s docstring, including the explicit "a scaffold call that rewrites the author SILENTLY does not satisfy OQ-02". NO EXISTING PLAN FILE WAS REWRITTEN: `git status --porcelain -- .aw/records/plans/` lists ONLY this plan itself (the lifecycle edit this execution is making), and none of the 274 parenthesized `- Author:` lines was touched, as the item requires. 7 new tests in `tests/test_ipd_lifecycle_cli.py::ScaffoldStopsWritingTheShapeItsOwnSetterRefuses`, all passing.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `grep -n '\[\^)\]\*' agent_workflows/*.py` output confirming the population, and the per-reader verdict table (symbol, file:line, verdict against BOTH spellings) covering every pattern and every derived consumer E-06 names. Paste the diff of the three prose copies of the old pattern, updated, plus the sentence explaining why the refusal remains correct after the widening. State explicitly that `ipd_schema.py:1266` was examined and left alone with the reason. Where a further broken reader was found, paste either its fix or the named follow-up. Paste the bare `python3 -m pytest` summary line and compare it to YOUR OWN measured baseline by node id, not to any figure written in this plan.
  - Observed evidence: THE SWEEP RE-RUN, confirming the review's population of five actor-bearing patterns plus the prose copies. BEFORE:
    ```text
    $ grep -n '\[\^)\]\*' agent_workflows/*.py
    agy_runipd.py:900:    the attribution lint's actor capture (`\(...[^)]*...\)`) would misparse ...   <- PROSE
    ipd_lifecycle.py:2139:  the actor with `\(([^)]*)\)`, so a parenthesized actor MISPARSES ...        <- PROSE
    ipd_lifecycle.py:2259/2268:  (the guard's own comment + message)                                    <- PROSE
    ipd_lint.py:180:  _HISTORY_ATTRIB_RE                                                                <- BROKEN, fixed by E-03
    ipd_schema.py:1266:  re.sub(r"\([^)]*\)", "", cleaned)                                              <- NOT an actor reader
    oc_runipd.py:866:  driver_actor docstring                                                           <- PROSE
    plan_readiness.py:343:  _HISTORY_RECORD_PARTS_RE                                                    <- BROKEN, fixed by E-08a
    record_history.py:293:  _TAIL_RE                                                                    <- BROKEN, fixed by E-08b
    ```
    AFTER: the only remaining `[^)]*` occurrences in `agent_workflows/` are `ipd_schema.py:1266` (deliberately untouched) and the three fixed patterns' own comments EXPLAINING what the old bound was and why it changed. `ipd_schema.py:1266` WAS EXAMINED AND LEFT ALONE, with the reason: it is `re.sub(r"\([^)]*\)", "", cleaned)` inside the E-item density heuristic, stripping parentheticals from an E-item's TEXT before counting action-verb clauses. It never sees an actor and never reads a history line, so widening it would change unrelated lint behavior.
    PER-READER VERDICT TABLE, every pattern and every derived consumer E-06 names, each exercised against BOTH spellings:
    ```text
    SYMBOL                                       LOCATION                   VERDICT (paren / slash)
    ipd_lint._HISTORY_ATTRIB_RE                  ipd_lint.py:195            OK actor='opencode (its_direct/model)' / OK actor='opencode/its_direct/model'
    plan_readiness._HISTORY_RECORD_PARTS_RE      plan_readiness.py:361      OK actor='opencode (its_direct/model)' / OK actor='opencode/its_direct/model'
    record_history._TAIL_RE                      record_history.py:308      OK actor='opencode (its_direct/model)' / OK actor='opencode/its_direct/model'
    ipd_lint._newest_executed_history            ipd_lint.py:868            OK ('opencode (its_direct/model)','did the work') / OK ('opencode/its_direct/model','did the work')
    ipd_lint._check_terminal_attribution         ipd_lint.py:887            OK 0 diagnostics / OK 0 diagnostics
    plan_readiness.is_review_history_entry       plan_readiness.py:373      OK True / OK True
    plan_readiness.newest_verdict                plan_readiness.py:396      OK 'negative' / OK 'negative'
    plan_readiness.approval_refusals             plan_readiness.py:443      OK 1 refusal / OK 1 refusal
    plan_readiness.is_plan_review_approved       plan_readiness.py:297      OK False / OK False
    record_history._parse_record_line            record_history.py:331      OK 'executed' / OK 'executed'
    ipd_lifecycle._plan_status_events            ipd_lifecycle.py:753       OK ['executed'] / OK ['executed']
    ipd_lifecycle.derive_plan_status             ipd_lifecycle.py:792       OK 'executed' / OK 'executed'
    attention_contract.HISTORY_RECORD_RE         attention_contract.py:537  SAFE (date-prefix only), matches both - NOT "fixed"
    plan_readiness.extract_newest_history_entry  plan_readiness.py:185      SAFE (whole-record), returns the record verbatim for both
    plan_readiness.history_verdict_approves      plan_readiness.py:207      SAFE, correctly False for a parenthesized REJECT under both
    ipd_schema (parenthetical strip)             ipd_schema.py:1266         N/A - not an actor reader; LEFT ALONE (reason above)
    ```
    Every reader now returns the SAME answer for both spellings, which is the property the whole plan is for. THE THREE PROSE COPIES ARE UPDATED, since each described a bound the code no longer has:
    ```diff
    # ipd_lifecycle.py (rollup_history_message docstring)
    -    the actor with `\(([^)]*)\)`, so a parenthesized actor MISPARSES and the attribution lint then
    -    fails. Today's `--actor "aw oc run (orchestrator rollup)"` is exactly that bug (F-4); ...
    +    THE REASON CHANGED, and the rule did not (plan fn2l1u). This used to say the readers' actor
    +    capture was bounded by `[^)]*` so a parenthesized actor MISPARSED; that is no longer true -
    +    ... all capture the actor LAZILY now and parse either shape. The parenthesis-free rule stands
    +    anyway, and is now ENFORCED at the setter (`attention_contract.actor_refusal`) ...
    # oc_runipd.py + agy_runipd.py (driver_actor docstrings), same correction:
    -    the attribution lint's actor capture (`\(...[^)]*...\)`) would misparse a parenthesized actor,
    +    The readers no longer REQUIRE this - plan fn2l1u made every actor capture lazy, so a
    +    parenthesized actor parses - but the setter now REFUSES one ...
    ```
    WHY THE REFUSAL REMAINS CORRECT AFTER THE WIDENING, stated in the code rather than assumed (on `actor_refusal` and in all three docstrings): the readers are now tolerant, so the guard no longer props up a parser limitation; it enforces the CONVENTION instead - every writer in the toolkit emits the parenthesis-free `key=value` shape, one shape is cheaper to read and grep than two, a nested-paren actor is ambiguous to a human skimming `- <date> <status> (<actor>): <msg>`, and refusing at the setter keeps the failure BEFORE the lifecycle commit rather than after it, which is the entire defect being closed.
    ONE FURTHER BROKEN READER WAS FOUND AND IS NAMED AS A FOLLOW-UP RATHER THAN FIXED: `ipd_lifecycle._plan_status_events` (`:753-774`) `reverse()`s file order on the assumption that history is stored newest-first, and 36 tracked plans are stored oldest-first, so a derived status can be wrong for those files. It is not reached by any gate today (the one consuming rule is pending-only) and fixing it is a larger behavior change than three regex bounds. Recorded as decision D5 with the symbol named. TWO residues are deferred BY NAME so they cannot read as a failed fix: the 150 multi-word-middle records (pinned by a deliberate test, `test_a_multi_word_middle_is_still_NOT_parsed`) and the 274 existing parenthesized `- Author:` lines.
    BARE SUITE, ACTUAL OUTPUT, compared to MY OWN baseline by NODE ID:
    ```text
    baseline (HEAD fea2c9f8, before any edit): 1 failed, 6828 passed, 3 skipped, 2 xfailed in 76.18s
    after this change:                         1 failed, 6864 passed, 3 skipped, 2 xfailed in 70.89s
    FAILED (both runs, identical node id):
      tests/test_orchestrator_retirement.py::RealRepositorySets::test_lanectn_refuses_naming_its_one_unfinished_child
    delta: +36 passed (exactly the new tests), SAME single failure, no new failure
    ```
    THAT FAILURE IS PRE-EXISTING AND UNRELATED, proven rather than asserted: with my `agent_workflows/` changes stashed it fails identically at clean HEAD (`AssertionError: True is not false`, same line `:876`). It is a corpus-state assertion about Set `lanectn`'s membership, which real work has moved on since the test was last re-measured; the test's own docstring instructs re-measuring rather than loosening, and that belongs to whoever owns `lanectn`, not to this plan. NOTE ON THE BASELINE METHOD, since it materially affects any comparison: run bare in this lane the suite reports 18 failures, because the driver sets `AW_EXECUTION_ROLE=worker` in my environment and 17 tests legitimately assert the runner-owned begin/finalize refusals and the driver's own non-worker env. Every figure above was therefore measured with `env -u AW_EXECUTION_ROLE`, which is the honest baseline for a lane-executed plan; the plan's own predicted baseline (`test_reporting_contract` failing on a gitignored dump) did NOT reproduce here at all.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was reviewed by `/plan-review` on 2026-09-09 and is `reviewed`; it must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. Two things a reader should carry into execution. FIRST, the plan's original central discovery holds and is what makes E-01/E-02 cheap: the guard already exists in `retire_orchestrator` and is being lifted rather than invented (F-3), though the review corrected WHERE it must be called (F-4: one choke point with three callers, not four unguarded paths). SECOND, and this is what the review changed: the highest-value item in the plan is now E-07, not E-01. The wedged finalize the backlog item reported is the VISIBLE half of the defect; the invisible half is that the same broken bound turns the approval gate's one un-overridable refusal into a no-op (F-12, reproduced end to end), which is the failure `apprvguard` was built after. An executor who runs out of room should do E-01, E-07, E-08a and stop, because that ordering fixes the gate; doing E-03 alone fixes only a lint.

Execution ordering note, since the dependency edges permit a wrong order: E-04's before/after measurement is only meaningful once BOTH E-03 and E-08 have landed, because two of its three consumers are E-08's. Do not run E-04 after E-03 alone and call it done.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD: this plan changes the actor validation that its OWN `aw ipd finalize` will run, so use the slash form for its own finalize and never reach for `--no-verify`, which is the habit this plan exists to remove. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
