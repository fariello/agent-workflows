# IPD: Make a selector that matches no artifact say so instead of printing an empty view and exiting 0

- Date: 2026-09-17
- Kind: child
- Concern: `aw attention <selector>` cannot tell the operator apart from a typo. A selector that resolves to NO artifact prints nothing and exits 0, which is byte-identical to a selector that resolved fine and legitimately has nothing to report. Measured 2026-09-17: `aw att zzzzzz` prints an empty view, exit 0; and in `--agent` mode BOTH a nonexistent selector and one that matched an artifact emit `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`, so a machine consumer records a typo as a clean audit. THE MATCHED-BUT-EMPTY TWIN IS NOT THE PARKED CASE, corrected at review from a real measurement: a selector FORCES `show_all` (`attention.py:3071`), so `aw att sv0sf3` DOES print its parked item and the two cases differ by one line. The genuine matched-but-empty case is a token that matches and is then removed by a DOWNSTREAM filter: measured, `aw att sv0sf3 -t plans` prints nothing and exits 0, exactly like `aw att zzzzzz`, and so do `aw att sv0sf3 --status ready` and `aw att reviewloc -t plans`. That is the case the fix must not mislabel, and it is the case an in-filter match fact gets WRONG, because `--type` is applied BEFORE the selector filter (`:2797-2799` then `:2806-2808`). The maintainer hit the no-match half twice in one session on `4fodkt` and `63425h`, each time asking "where is this invisible plan?" and each time the answer required a human to go and grep. A read-only reporting verb that answers a question it did not actually answer is worse than one that refuses.
- Scope: Make `aw attention` distinguish NO-MATCH from MATCHED-BUT-EMPTY for EVERY selector form it accepts (id6, setid, path, tree, status, priority, attention class, substring), report the no-match case explicitly on EVERY output surface the verb has (human board, `--agent`, `--json`/`--format json`, `--check`, and the three list modes `-id`/`--paths`/`--filenames`), and choose the exit code deliberately. Does NOT change which artifacts are shown, the attention classes, the default hiding of terminal/parked items, or any other verb's selector handling.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py, agent_workflows/cli.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: attsel
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: fqnj8k
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-17 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; 12 findings PR-001..PR-012 all FIXED in place; readiness go-pending-approval; typed review record .aw/records/reviews/20260917-attsel-01-fqnj8k-...review.md

- 2026-09-17 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-012 all FIXED. Reviewed at HEAD `cf0ebf7a`; `aw ipd lint --phase author` conforming before revision (one `IPD-Z602` density advisory on E-05, addressed by splitting it into E-05/E-09/E-10). THE CENTRAL DEFECT REPRODUCES: `aw att zzzzzz` -> 1 blank line, exit 0, and `--agent` -> `outcome:clean, exit:0, findings:0`, identical to a successful selector. BUT THE PLAN'S OWN AMBIGUITY FIXTURE WAS WRONG, and it was the specification for E-01/E-03/V-01: a selector FORCES `show_all` (`attention.py:3071`), so `aw att sv0sf3` DOES show its parked item (measured: 2 lines vs 1). The real matched-but-empty twin is a DOWNSTREAM-FILTERED match (`aw att sv0sf3 -t plans` -> empty, exit 0), which also breaks E-03's premise, since `--type` filters the item list BEFORE the selector filter sees it (`:2797-2799` then `:2806-2808`), so a match fact computed inside the filter reports a FALSE no-match for it (measured: filter over the full 1063-item scan matches 1, over the `-t plans` 661-item scan matches 0). Also found: FIVE further output surfaces the plan never named (`--json`/`--format json`, `--check`, `-id`, `--paths`, `--filenames`), all silent today; a VOCABULARY class of legitimate zero-match tokens (`abandoned`, `reusable`, `planned`, `roadmaps`, `releases` as a tree) that the fail-closed default would newly make nonzero; and a repository PRECEDENT that answers OQ-01 (spec `25kzda` Section 2.3/2.4a: zero matches exit 2, status selectors exempt). E-01..E-06 rewritten, E-07..E-10 added, `Highest E allocated` 06 -> 10, `cli.py` added to the fence for the `--help` exit contract. Readiness `go-pending-approval`.
- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from a defect the maintainer hit twice in one session and then asked to be filed rather than described in chat. MEASURED AT AUTHORING, all reproducible at HEAD `2aad4a98`: `aw att zzzzzz` -> no lines, exit 0; `aw att nosuchid` -> same; `aw att nosuchset-01` -> same; `aw att tests/nope.py` -> same; and the ambiguity proof, `aw att sv0sf3` (the real parked item `.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-...`) -> one line, exit 0, versus `aw att zzzzzz` -> zero lines, exit 0. In `--agent` mode both a real selector and a nonexistent one emit the identical `outcome:clean, exit:0, verified:true, complete:true, findings:0` record. THE CAUSE IS LOCATED, not guessed: `attention.filter_items_by_selectors` (`agent_workflows/attention.py:2635`) resolves each token against eight record types inside a bare `except Exception: pass`, collects matches into `matched_paths`, and returns a filtered LIST. A token that matched nothing is indistinguishable in that return value from a token whose matches were all filtered out downstream, and the caller (`:2806-2808`) simply replaces `items` with the result.

## Goal

Answer the operator's actual question. When they type a selector, they are asking "what is the state of
this thing?"; if the thing does not exist, that is the answer, and it is not the same answer as "nothing
needs attention."

THREE FACTS ESTABLISHED AT REVIEW, so the executor does not re-derive them and does not inherit the
authoring-time fixture that was wrong.

1. A SELECTOR ALREADY FORCES `show_all`. `attention.py:3071` (and its twins at `:2850` and `:2991`)
   compute `show_all = args.all or bool(selectors_arg) or has_terminal_status`, so an artifact in a
   hidden class IS shown when named. Measured: `aw att sv0sf3` prints its parked item (2 lines) while
   `aw att zzzzzz` prints 1 blank line. The plan's original "matched but hidden" fixture therefore did
   not exist, and the "do not auto-enable `--all`" caution was guarding a behavior already in place.
2. THE REAL MATCHED-BUT-EMPTY CASE IS A DOWNSTREAM-FILTERED MATCH. Measured empty-and-exit-0:
   `aw att sv0sf3 -t plans`, `aw att sv0sf3 --status ready`, `aw att reviewloc -t plans`. These are the
   cases that MUST NOT be reported as a no-match, and they are why the distinction is worth building.
3. THE MATCH FACT CANNOT BE COMPUTED INSIDE `filter_items_by_selectors`. `--type` narrows `items`
   BEFORE the call (`:2797-2799`, then `:2806-2808`), so the filter never sees the artifact a token
   matched. Measured with the real scan: the filter over the full 1063-item scan matches `sv0sf3`
   (1 item); over the `-t plans` 661-item scan it matches 0. A match fact derived from what the filter
   received would report `sv0sf3` as a NO-MATCH under `-t plans`, which is exactly the false-negative
   F4 warns about, arriving through a route F4 did not name. THE MATCH FACT MUST BE COMPUTED AGAINST
   THE UNFILTERED SCAN, which means either capturing `items` before the type filter or passing the
   unfiltered list in explicitly.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the two cases before changing any output

- [ ] E-01 REPRODUCE THE AMBIGUITY AS A TEST FIRST, using the CORRECTED fixture, so the fix has a falsifiable target. The three cases are: (a) a nonexistent token, (b) a token that MATCHES an artifact which a DOWNSTREAM filter then removes, and (c) a token that matches a visible artifact. Assert that (a) and (b) are indistinguishable today in visible line count, exit code, and the `--agent` `outcome`/`exit`/`findings` triple, and that (c) differs. DO NOT USE "matched but hidden" FOR (b): a selector forces `show_all` (`attention.py:3071`), so a named parked artifact IS shown, and the authoring-time fixture that claimed otherwise was wrong (Goal fact 1). Build (b) from a real downstream filter, e.g. a token matching a backlog artifact plus `-t plans`, and re-derive the artifact at execution time rather than trusting an id in this plan.
  - Depends on: none
  - Expected outcome: a pasted test run showing (a) and (b) currently indistinguishable in human output, exit code, and agent record, and (c) distinguishable; with the concrete invocation used for (b) named.
  - Execution state: pending

- [ ] E-02 ENUMERATE EVERY SELECTOR FORM `filter_items_by_selectors` ACCEPTS, from the code rather than from this plan, and state per form how a NO-MATCH is currently detectable (it is not). Read `agent_workflows/attention.py:2635-2693`: the token is resolved against eight record types via `selectors.resolve_selectors`, then compared against `it.id`, `it.tree`, `it.attention_class`, `it.native_status`, `it.priority`, and finally a substring match on `it.path`. The substring rung is the one that matters most for this fix and is easy to miss: it means a token can match an artifact WITHOUT resolving as an identifier at all, so "did the selector resolve?" and "did the selector match?" are different questions and the fix must key on the second. Note the converse too, measured at review: `.aw` and `zzzzzz` resolve to nothing yet `pending`, `executed` and `graduated` resolve to real artifacts AND match hundreds more by path substring, so resolution and match disagree in BOTH directions.
  - Depends on: none
  - Expected outcome: a pasted per-form table (form, where it is matched in the code, whether a no-match is currently reported), with the substring rung called out explicitly and at least one token shown resolving-but-under-matching and one matching-without-resolving.
  - Execution state: pending

- [ ] E-07 ENUMERATE EVERY OUTPUT SURFACE `aw attention` HAS, and pin which ones this plan will change. Measured at review, ALL of these are silent on a nonexistent selector and exit 0: the human board, `--agent`, `--json`, `--format json`, `--check` (which prints "the view is valid", the most actively misleading of the set), `-id`/`--id6-only`, `--paths`, and `--filenames`. The plan as authored named only the first two. The three list modes return early at `attention.py:3012` and `--check` returns at `:2983`, both BEFORE the human board is ever composed, so a message appended to the board reaches neither. Decide and record which surfaces carry the report and which deliberately do not, with the reason per surface: a list mode exists to be piped into another command, so a diagnostic on STDOUT would corrupt the pipe and STDERR is the correct channel there.
  - Depends on: none
  - Expected outcome: a pasted table of all eight surfaces with the measured current behavior (output and exit code) and the decided target behavior per surface, including the channel (stdout/stderr) and the reason for any surface deliberately left unchanged.
  - Execution state: pending

- [ ] E-08 ENUMERATE THE LEGITIMATE ZERO-MATCH VOCABULARY TOKENS and decide their treatment BEFORE implementing the exit code, because the fail-closed default would newly make them nonzero. `aw attention` accepts tree names, attention classes, and native statuses as selectors, and a repository can legitimately contain none of a given value. Measured at review in THIS repo, all currently empty and exit 0: `abandoned`, `reusable`, `planned`, `roadmaps`, and `releases` as a TREE token (the tree is declared tracked but `TRACKED_TREES` is `('specs','plans','research','backlog','releases')` while the live scan yields only four trees, so `roadmaps` matches nothing by tree at all). This is not a typo class: it is the same distinction spec `25kzda` Section 2.4a already draws, where a STATUS selector matching nothing is a success because it is "a standing question about repository state rather than an assertion that a named item exists", while a misspelled id6 is an error. Decide whether a vocabulary token is exempt from the nonzero treatment, and derive the vocabulary from the contract symbols (`attention_contract.TRACKED_TREES`, `ATTENTION_CLASSES`, and the per-tree status enums) rather than a hand-written literal list, so a value added later cannot silently become an "error".
  - Depends on: E-02
  - Expected outcome: the vocabulary set derived from contract symbols and pasted, the exemption decision recorded with `25kzda` Section 2.4a cited, and each measured token above shown under the decided treatment.
  - Execution state: pending

### Task group 2: report the no-match case, per token, without changing what is shown

- [ ] E-03 COMPUTE PER-TOKEN MATCH FACTS AGAINST THE UNFILTERED SCAN, not inside `filter_items_by_selectors` as authored. THE AUTHORED PLACEMENT IS WRONG AND WOULD SHIP THE FALSE NO-MATCH F4 WARNS ABOUT: `--type` narrows `items` before the filter is called (`:2797-2799`, then `:2806-2808`), so a token matching a backlog artifact under `-t plans` reaches the filter with its artifact already gone. Measured at review: the same filter matches `sv0sf3` over the full 1063-item scan and 0 items over the `-t plans` 661-item scan. So capture the scan output BEFORE any filter and answer, per token, "did this token match at least one artifact in the UNFILTERED scan?". Keep `filter_items_by_selectors`'s current signature and return value working unchanged so its six existing assertions (`tests/test_attention.py:439-471`) still pass; add the facts as a separate pure function or an explicit second return, not as a mutation of the existing contract. Two facts are worth separating (per F3): "this token matched nothing" and "this token is not a valid selector at all" (the resolver raised, currently swallowed at `:2659-2661`).
  - Depends on: E-01, E-02
  - Expected outcome: a pure, tested match-facts function pasted, with a test proving it reports MATCHED for a token whose artifact is removed by a downstream `-t` filter (the regression that the authored placement would have failed), plus the six existing `filter_items_by_selectors` assertions shown still green.
  - Execution state: pending

- [ ] E-04 REPORT A NO-MATCH SELECTOR IN THE HUMAN OUTPUT, naming the token and saying plainly that no artifact matched it. Where SOME tokens matched and others did not, report the unmatched ones individually rather than collapsing to one message, because a multi-token invocation is exactly where a single typo hides. Say what was searched (the tracked record trees) so the message is actionable rather than a bare negative. Do NOT print a remedy that guesses at intent (no "did you mean"): a wrong guess is worse than none, and the operator knows what they typed. REUSE THE EXISTING EMPTY-STATE PRIMITIVE rather than inventing a message shape: `term.Term.format_empty_result` (`agent_workflows/term.py:588`) already renders an outcome line, an "Active filters:" block echoing the selector, and a `Next` action, and `aw find` already uses it for its own empty result, so a second hand-rolled shape here would diverge from a house pattern the operator already reads.
  - Depends on: E-03, E-07
  - Expected outcome: pasted output for a nonexistent selector naming the token; for a mixed invocation naming only the unmatched token(s); for a DOWNSTREAM-FILTERED match shown NOT reported as a no-match; and for an all-matching invocation unchanged from today, shown side by side.
  - Execution state: pending

- [ ] E-05 MAKE THE `--agent` RECORD SAY IT TOO, which is the half that matters most for automation and is currently the most misleading. Today a nonexistent selector emits `outcome:clean, verified:true, complete:true, findings:0`, so a consumer records a typo as a clean audit. The record must distinguish the two cases in a machine-readable field rather than only in prose. VERIFIED AT REVIEW that a valid representation exists, so no schema change is needed and none may be made: `agent_schema.validate_agent_record` returns `[]` for `outcome:findings, exit:1` and for `outcome:cannot-run, exit:2` on a `result` record, and the repository already ships the `cannot-run`/exit-2 shape for an unresolvable read-only target (`aw runs zzzzzz --agent` emits `kind:error, outcome:cannot-run, exit:2, verified:false, complete:false, unresolved_targets:["zzzzzz"]`). Prefer following that existing precedent, including its `unresolved_targets` field name, over inventing a third convention. Verify with the schema validator, not by eye.
  - Depends on: E-03, E-06
  - Expected outcome: the agent record for a no-match selector pasted, distinguishable from the matched-but-empty record, and shown passing `agent_schema.validate_agent_record` (the call and its actual `[]` result pasted), with the chosen shape compared against the `aw runs` precedent.
  - Execution state: pending

- [ ] E-09 CARRY THE DISTINCTION INTO `--json`/`--format json`, which is the surface `/whatnext` consumes as its PRIMARY source (`.aw/system/workflows/whatnext/whatnext.md:50` runs `aw attention --format json` first). Its payload has a top-level `valid` flag derived solely from the drift list (`render_json`, `attention.py:1258`), so today a typo yields `valid:true, items:[]` and an agent reading it concludes the repository is fine and has nothing matching. Decide whether an unmatched token belongs in `violations` (which would flip `valid` and is a schema-visible behavior change) or in a NEW top-level key, and bump `SCHEMA_VERSION` if the payload shape changes, since the field is versioned for exactly this. Do not leave this surface behind: an agent-facing payload that says `valid:true` about a question it did not answer is the same defect as the `--agent` one.
  - Depends on: E-03, E-05
  - Expected outcome: the `--json` payload pasted for a no-match and for a matched-but-empty selector, visibly different; the `valid`/`SCHEMA_VERSION` decision stated with its reason; and the `/whatnext` consumer's reading of the new payload described.
  - Execution state: pending

- [ ] E-10 FIX `--check` AND THE THREE LIST MODES, the surfaces that return before the board is composed and would otherwise keep their current silence. `--check` is the worst case measured: `aw att zzzzzz --check` prints "aw attention --check: the view is valid." and exits 0, actively asserting validity about a token it never found, and it returns at `attention.py:2983` (agent branch at `:2976`). The three list modes return at `:3012`. For `--check`, decide whether an unmatched token is a VIOLATION (it would then flow through `core.drift_exit_code` and fail the CI gate at `.github/workflows/tests.yml:145`, which runs `attention --check --agent` with NO selector and is therefore unaffected either way) or a separate refusal, and state which. For the list modes, emit the report on STDERR and keep STDOUT byte-identical so a pipe is not corrupted.
  - Depends on: E-03, E-06, E-07
  - Expected outcome: pasted before/after for `--check`, `-id`, `--paths` and `--filenames` with a nonexistent selector, showing the message, the channel it went to, the exit code, and (for the list modes) STDOUT proven byte-identical; plus the bare `attention --check --agent` CI invocation shown unchanged.
  - Execution state: pending

- [ ] E-06 DECIDE AND IMPLEMENT THE EXIT CODE for a no-match selector, and state the reasoning in the code rather than only in this plan. THE REPOSITORY HAS ALREADY RULED ON THIS QUESTION for its selector-resolving verbs, which OQ-01 did not know: spec `25kzda` (`Status: approved`) Section 2.3 states "Zero matches return exit 2", and Section 2.4a makes exactly one exemption, for STATUS selectors, on the ground that a status token is "a standing question about repository state rather than an assertion that a named item exists", closing with "A misspelled id6 still exits 2; only the status selectors are exempt". That spec governs `aw <host> run`, not `attention`, so it is PRECEDENT rather than binding contract; adopt its shape unless there is a stated reason not to, and record which you did. Implement the FAIL-CLOSED form (nonzero for a no-match on a non-vocabulary token) with the E-08 exemption applied, and make the code comment name the rejected alternative and cite the precedent so a later reader sees it was a decision. NOTE the exit code is currently `core.drift_exit_code(drift)` at three return sites (`:3012`, `:3238`, and the `--check` path at `:2983`); a no-match code must compose with a DRIFTY view rather than overwrite it, since this repository's view is drifty today (measured: bare `aw att --agent` -> `outcome:findings, exit:1, findings:21`).
  - Depends on: E-04, E-08
  - Expected outcome: the chosen exit code implemented and pinned by a test for all three fixture cases plus a vocabulary token, with the reasoning, the `25kzda` precedent, and the rejected alternative recorded at the decision site in the code, and the drift-composition behavior pinned by its own test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SUBSTRING RUNG MAKES "RESOLVED" AND "MATCHED" DIFFERENT QUESTIONS. `filter_items_by_selectors` ends with `if tok_lower in it.path.lower()` (`attention.py:2688`), so a token that resolves as no identifier can still legitimately match by path fragment. A fix that only asked `selectors.resolve_selectors` whether the token resolved would report a false no-match for every substring query.
- THE RESOLVER FAILURE IS ALREADY SWALLOWED. The per-record-type resolution sits inside `except Exception: pass` (`:2659-2661`), which is why a malformed selector is silent rather than refused. E-03 must not remove that tolerance (a raising resolver should not break the view) but must stop it from being indistinguishable from a clean answer.
- FAIL-CLOSED ON A DANGLING REFERENCE IS THE HOUSE PATTERN. `aw check` flags a `From-Backlog` or `From-Spec` value that resolves to no artifact (`check.from-backlog-dangling`, `check.from-spec-dangling`), and `AGENTS.md` records that a broken handoff claim is an error either way. A selector naming nothing is the same class of claim.
- AN UNRESOLVABLE READ-ONLY TARGET ALREADY REFUSES ELSEWHERE, with a shape to copy. `aw runs <bogus>` exits 2 on BOTH surfaces and its `--agent` record is `kind:error, outcome:cannot-run, exit:2, verified:false, complete:false, findings:1, unresolved_targets:["zzzzzz"]`; its help text states the rule and the reason ("A target that matches no run is an error naming the token, not an empty success", `cli.py:2082`) AND the deliberate exemption ("A bare `aw runs` in a repository with no runs is still exit 0: asking for everything and finding nothing is not a failed request"). That is this plan's problem, already solved once, including the vocabulary exemption E-08 needs.
- BUT `aw find` DOES THE OPPOSITE, and the divergence is worth knowing before choosing. `aw find plans zzzzzz` prints `✓ CLEAN  no matching plans` with the selector echoed under "Active filters:" and exits 0, both human and `--agent`. So the repository has BOTH conventions live: refuse (`aw runs`) and report-cleanly (`aw find`). `aw find`'s message is at least explicit about having found nothing, which is more than `attention` does; the exit-code question is genuinely open across the codebase, which is why E-06 must record its choice rather than assume one house rule exists.
- `aw attention` IS READ-ONLY AND MUST STAY SO. `AGENTS.md` describes it as computing the view ON DEMAND with nothing committed. This plan adds output and possibly an exit code; it writes nothing.
- DEFAULT HIDING IS DELIBERATE BUT A SELECTOR ALREADY OVERRIDES IT. Terminal and `parked` artifacts are hidden until `--all` by design, AND `show_all` is already forced by any selector (`:2850`, `:2991`, `:3071`), so naming an artifact shows it. The fix therefore needs no change here at all, and the authored caution against "auto-enabling `--all`" describes a behavior that already exists.
- THE ORDER OF FILTERS IS LOAD-BEARING FOR THIS FIX. `run()` applies `--type` (`:2797`), then selectors (`:2806`), then `--status` (`:2829`), `--priority` (`:2832`), `--blocking`, `--readiness`, `--open-questions` and `--arcive-state`. Anything computed from the list the selector filter RECEIVES is already narrowed by `--type`; anything computed from what it RETURNS is not yet narrowed by the six filters after it. Both directions produce a wrong match fact, which is why E-03 pins the fact to the unfiltered scan.
- `SCHEMA_VERSION` IN `--json` IS THE VERSIONING LEVER, currently 4 (`attention.py:1256`, emitted as `schema_version`). E-09 changes that payload, so the bump belongs there rather than being discovered by a consumer.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `attention.filter_items_by_selectors` | **A NO-MATCH SELECTOR IS INDISTINGUISHABLE FROM A CLEAN ANSWER.** `aw att zzzzzz` prints one blank line and exits 0, byte-identical to `aw att sv0sf3 -t plans` (a token that DOES match, narrowed away downstream). The operator cannot tell a typo from a quiet repo, and the only recovery is to leave the tool and grep. | re-measured at review HEAD `cf0ebf7a`; `attention.py:2635` returning a bare filtered list |
| F1a | HIGH | this plan's own original fixture | **THE AUTHORED AMBIGUITY FIXTURE WAS WRONG, and it was the specification for E-01, E-03 and V-01.** The claim "`aw att sv0sf3` prints a line and exits 0, same as `aw att zzzzzz`" treated a MATCHED-AND-SHOWN case as the matched-but-empty twin. A selector forces `show_all`, so the two differ (2 lines vs 1) and the original three-way fixture could not have distinguished anything. Corrected in the Concern, the Goal and E-01; the real twin is a downstream-filtered match. | `attention.py:3071`; measured `aw att sv0sf3` = 2 lines, `aw att zzzzzz` = 1 line; `aw att sv0sf3 -t plans` = empty, exit 0 |
| F2 | HIGH | the `--agent` record | **AUTOMATION RECORDS A TYPO AS A CLEAN AUDIT.** Both a matching and a nonexistent selector emit `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`. `verified:true` and `complete:true` are both false in substance for a selector that matched nothing: nothing was verified and the answer is not complete, it is absent. | pasted agent records for `aw att zzzzzz --agent` and `aw att sv0sf3 --agent`, identical envelopes |
| F3 | MEDIUM | `attention.py:2659-2661` | The resolver runs inside `except Exception: pass`, so a MALFORMED selector is as silent as a merely-absent one. Worth separating in the fix: "this token is not a valid selector" and "this valid token matched nothing" are different messages, and conflating them would trade one ambiguity for another. | the bare except in the record-type loop |
| F4 | MEDIUM | `attention.py:2688` | THE SUBSTRING RUNG IS THE TRAP FOR THIS FIX. A token can match by path fragment without resolving as any identifier, so "did it resolve?" is the WRONG question. Keying the no-match report on the resolver alone would report a false no-match for every substring query, which is a worse defect than the one being fixed. | the final `if tok_lower in it.path.lower()` rung; measured, `.aw` resolves to nothing while `pending`/`executed` resolve AND over-match by path |
| F5 | LOW | `agent_schema` | **WITHDRAWN AT REVIEW: THE HONEST RECORD DOES FIT.** `validate_agent_record` returns `[]` for `outcome:findings, exit:1` and for `outcome:cannot-run, exit:2` on a `result` record, both measured, and `aw runs` already ships the second shape for exactly this condition. The concern was that no valid representation existed; two do, so E-05 may not bump the schema and must reuse the precedent. Left in place rather than deleted so the reasoning stays auditable. | measured `validate_agent_record` -> `[]` for both shapes; `aw runs zzzzzz --agent` -> `cannot-run`/exit 2/`unresolved_targets` |
| F6 | LOW | this session's own history | THE COST IS REAL AND WAS PAID TWICE IN ONE SITTING. The maintainer ran `aw att 4fodkt` and `aw att 63425h`, got silence both times, and had to ask "where is this invisible plan?" Both were genuinely absent from `main` (an agent's unmerged worktree), so the tool was right that nothing matched and wrong to say nothing about it. | the session transcript; both now resolve at review HEAD, confirming they were absent rather than misnamed |
| F7 | HIGH | `attention.py:2797-2808` | **THE AUTHORED FIX SITE COMPUTES A FALSE NO-MATCH, arriving by a route F4 did not name.** E-03 as authored put the match fact inside `filter_items_by_selectors`, but `--type` narrows `items` BEFORE the call, so the filter never sees the artifact a token matched. Measured: the filter matches `sv0sf3` over the full 1063-item scan and 0 items over the `-t plans` 661-item scan, so `aw att sv0sf3 -t plans` would have been reported as a TYPO. That is the exact worse-than-the-bug outcome the execution contract calls mandatory to avoid. | measured with the real scan through `att.scan` + `att.parse_type_filters(['plans'])` + `att.filter_items_by_selectors` |
| F8 | HIGH | five unnamed output surfaces | **FIVE SURFACES WERE OUT OF THE PLAN AND ALL ARE SILENT.** `--json`, `--format json`, `--check`, `-id`, `--paths`, `--filenames` all print nothing (or `valid:true`) and exit 0 for a nonexistent selector. `--check` is the worst: it prints "aw attention --check: the view is valid." A board-level message reaches none of them, because `--check` returns at `:2983` and the list modes at `:3012`, before the board is composed. Now E-07, E-09 and E-10. | measured all eight surfaces with `aw att zzzzzz <flag>`; return sites at `:2983`, `:3012` |
| F9 | MEDIUM | `render_json` / `/whatnext` | **THE `--json` PAYLOAD IS WHAT `/whatnext` READS FIRST, and it asserts `valid:true` for a typo.** `.aw/system/workflows/whatnext/whatnext.md:50` names `aw attention --format json` as the PRIMARY source, run first; its `valid` flag comes only from the drift list (`:1258`), so an agent driving the repository's own "what should I do next" workflow off a mistyped selector is told the repository is valid and empty. | `whatnext.md:50`; `attention.py:1258`; measured `aw att zzzzzz --json` -> `valid: true, items: []` |
| F10 | MEDIUM | vocabulary selectors | **A FAIL-CLOSED DEFAULT WOULD MAKE LEGITIMATE EMPTY QUESTIONS INTO ERRORS.** `abandoned`, `reusable`, `planned` and `roadmaps` all match nothing in THIS repository today and exiting nonzero for them would be wrong: asking "what is abandoned?" and hearing "nothing" is a successful answer. Spec `25kzda` Section 2.4a already draws this line for status selectors and states the reason. Unaddressed as authored; now E-08, and E-06 depends on it. | measured five zero-match vocabulary tokens; `25kzda` Sections 2.3 and 2.4a; `attention_contract.TRACKED_TREES` = 4 live trees vs `roadmaps` declared |
| F11 | MEDIUM | OQ-01 | **OQ-01 ASKED A QUESTION THE REPOSITORY HAS ALREADY ANSWERED once, and answered the other way once.** Spec `25kzda` (approved) Section 2.3 rules "Zero matches return exit 2" with one status-selector exemption; `aw runs` implements exactly that; `aw find` does the opposite (exit 0 with an explicit empty-result message). Neither governs `attention`, so the question stays the maintainer's, but it is now a choice between two named live conventions rather than an abstract trade-off. | `25kzda:205`, `:239`; `cli.py:2082`; measured `aw runs zzzzzz` exit 2 vs `aw find plans zzzzzz` exit 0 |
| F12 | LOW | `attention.py:3012`, `:3238`, `:2983` | THE EXIT CODE HAS THREE RETURN SITES AND THE VIEW IS DRIFTY TODAY. All three return `core.drift_exit_code(drift)`, and a bare `aw att --agent` in this repository already reports `outcome:findings, exit:1, findings:21` (stranded lanes). A no-match code must COMPOSE with that rather than overwrite it, or a no-match on a drifty view would mask 21 real findings. Unstated as authored; now in E-06. | the three return sites; measured bare `aw att --agent` |

## Proposed changes (ordered, validatable)

1. Pin the CORRECTED three-way fixture (E-01), enumerate every selector form (E-02), every output surface (E-07), and the legitimate zero-match vocabulary (E-08).
2. Compute per-token match facts against the UNFILTERED scan, leaving `filter_items_by_selectors`'s contract intact (E-03).
3. Report unmatched tokens individually in human output through the existing empty-state primitive, with no intent-guessing (E-04).
4. Make the agent record distinguish the two cases using the `aw runs` precedent, validated against the schema (E-05).
5. Choose the exit code deliberately with the `25kzda` precedent cited and the vocabulary exemption applied, compose it with the drift code, and record the rejected alternative in code (E-06).
6. Carry the distinction into `--json` (E-09) and into `--check` plus the three list modes (E-10), so no surface keeps the old silence.

## Deferred / out of scope (with reason)

- EVERY OTHER VERB'S SELECTOR HANDLING. The same ambiguity exists in `aw find` (measured: `aw find plans zzzzzz` -> `✓ CLEAN  no matching plans`, exit 0, both surfaces), and plausibly in `aw ipd board` and others, but each has its own output contract and exit-code meaning, and widening this plan to all of them would make one change to N contracts at once. `aw find` is at least EXPLICIT about having found nothing, which is the part `attention` lacks, so it is a lesser defect. If E-02 finds the shared resolver is the right fix point for all of them, that is a FINDING and a follow-up plan, not a silent widening.
- A "DID YOU MEAN" SUGGESTION. Deliberately excluded: a wrong guess is worse than a clean negative, and the operator knows what they typed. Fuzzy matching is a separate feature with its own design question.
- CHANGING WHICH ARTIFACTS ARE SHOWN. Default hiding is deliberate. Note this exclusion is NARROWER than it looks: a selector ALREADY forces `show_all` (`:3071`), so there is nothing to auto-enable and the authored version of this bullet described a change that was never needed.
- THE SPURIOUS `TODO: Run /aw setup-repo` LINE. NOT REPRODUCIBLE at review HEAD and re-scoped rather than carried as stated: the footer is gated on `setup_needed(repo_root)` (`attention.py:1606`), which reads the marker file `.aw/setup-repo-needed.md`; that file is absent here, `setup_needed` returns False, and no `aw att` invocation printed the line. So the authored claim that it prints "unconditionally, including on successful calls in a fully-configured repo" is false for this repo at this HEAD. If it was seen, the marker existed at the time, which is the feature working. Left deferred with the corrected diagnosis so it is not re-filed as a defect on a false premise.
- THE `roadmaps` AND `walkthroughs` TREES NOT APPEARING IN THE VIEW AT ALL. Measured: `attention_contract.TRACKED_TREES` is `('specs','plans','research','backlog','releases')` and a live `--all` scan yields items from only four trees (`plans`, `backlog`, `research`, `specs`), so `releases` records and every `roadmaps`/`walkthroughs` file are invisible to `aw attention` regardless of selector, and `aw att f33nrj` (a REAL release record) is empty even with `--all`. That is a genuine gap and it INTERACTS with this plan (those tokens must not be reported as typos), but it is `20260908-durablecapture-02-m867ox` (`Status: approved`) which owns it and declares `attention_contract.py` in scope. E-08 must handle the tokens WITHOUT editing the tree set, and must not race that plan.

## Scope check

- Over-scope: none. Every item is contained in the selector-to-output path of one verb. `cli.py` is in the fence only for the `--help` exit-contract text E-06 changes.
- Under-scope: closed at review. The five unreported output surfaces (F8, now E-07/E-09/E-10), the false-no-match fix site (F7, now E-03), and the legitimate zero-match vocabulary (F10, now E-08) were all missing. Still deliberately out: the other verbs, fuzzy suggestions, and the tracked-tree gap owned by `m867ox`, each deferred above with a reason.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). The gate is no NEW failures. Note for a managed worker lane: if `AW_EXECUTION_ROLE=worker` is set, lifecycle CLI tests refuse by design; say which form you ran and do not "fix" those tests.
2. E-01's CORRECTED three-way fixture, pasted before and after, showing the no-match case becomes distinguishable while the DOWNSTREAM-FILTERED matched-but-empty case is UNCHANGED.
3. A MULTI-TOKEN invocation where one token matches and one does not, showing only the unmatched one is reported.
4. A SUBSTRING selector (matching by path fragment, resolving as no identifier) shown NOT reported as a no-match: this is F4's regression guard and its absence would make the fix worse than the defect.
5. F7'S REGRESSION GUARD, which is mandatory for the same reason as item 4 and is the one the authored plan would have failed: a token whose artifact is removed by a downstream `-t`/`--status` filter shown NOT reported as a no-match. Assert it through the CLI path, not only against the pure function, since the ordering bug lives in `run()`.
6. All six existing `filter_items_by_selectors` assertions (`tests/test_attention.py:439-471`) shown still green, proving its contract was preserved.
7. Every surface from E-07's table exercised with a nonexistent selector: human, `--agent`, `--json`, `--format json`, `--check`, `-id`, `--paths`, `--filenames`. For the three list modes, STDOUT proven byte-identical to today.
8. The `--agent` record for both cases, shown passing `agent_schema.validate_agent_record` with the call and its actual return value pasted, not asserted.
9. A VOCABULARY token that legitimately matches nothing (e.g. `abandoned`) shown under the E-08 decision, with its exit code.
10. The DRIFT COMPOSITION case: a no-match selector on a view that also has drift, showing neither code masks the other.
11. The bare `python -m agent_workflows attention --check --agent` CI invocation (`.github/workflows/tests.yml:145`) shown unchanged.
12. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC CHANGE, and this was CHECKED at review rather than assumed. `aw attention`'s selector behavior is
verb behavior; searching the specs tree found no spec asserting an `attention` exit contract, and the one
spec that rules on zero-match selector semantics, `25kzda` (`Status: approved`, Sections 2.3 and 2.4a),
governs `aw <host> run` and never mentions `attention`. So it is PRECEDENT for E-06 to cite, not a contract
to amend, and `- Scope-Paths:` correctly declares no `.spec.md`. If the executor finds spec text this
review missed asserting that `attention` exits 0 whenever the view is valid, THAT is a contract this plan
changes: declare the spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and record
the reason here rather than changing behavior around it.

DOCUMENTATION IS IN SCOPE AND `cli.py` IS DECLARED FOR IT. `aw attention --help` currently documents
`--check` as "fails closed on an invalid view (CI gate)" and says nothing about a selector's exit meaning
(`cli.py:380-388`). If E-06 changes the exit code, or E-10 changes what `--check` refuses, update that text
in the SAME change: a verb whose help still promises the old contract is worse than one with no documented
contract. Follow the wording pattern `aw runs` already uses for this exact rule (`cli.py:2082`), which
states the refusal, the reason, and the deliberate exemption.

## Open questions

### OQ-01: Should a no-match selector exit nonzero, or exit 0 with the message?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the plan is executable under either answer and E-06 implements the FAIL-CLOSED form by default (nonzero), which is the safe direction and is trivially relaxed later. FOR NONZERO: the verb did not answer the question asked, and this repository already fails closed on a dangling reference (`check.from-backlog-dangling`); a script that greps for an id6 and gets exit 0 with empty output will conclude "nothing to do", which is exactly the wrong conclusion. FOR ZERO: `attention` is a read-only reporting verb whose exit code today means "the view is valid", scripts may already treat nonzero as "the repo is broken", and a typo is an operator error rather than a repository defect. Recorded rather than decided because it is a public-contract call on a verb the maintainer uses interactively many times a day.
- ADDED AT REVIEW, TWO LIVE PRECEDENTS, SO THIS IS A CHOICE BETWEEN NAMED CONVENTIONS RATHER THAN AN ABSTRACT TRADE-OFF (F11). NONZERO IS ALREADY THE RULED ANSWER for a selector-resolving verb here: spec `25kzda` (`Status: approved`) Section 2.3 states "Zero matches return exit 2", Section 2.4a exempts STATUS selectors only, with the reason ("a standing question about repository state rather than an assertion that a named item exists") and the closing "A misspelled id6 still exits 2; only the status selectors are exempt". `aw runs` implements exactly that, exit 2 on both surfaces, with the rule stated in its own help (`cli.py:2082`) including the bare-invocation exemption. ZERO IS ALSO LIVE: `aw find plans zzzzzz` prints `✓ CLEAN  no matching plans` and exits 0. Neither governs `attention`, so the call remains the maintainer's; what has changed is that E-06 must now cite which convention it followed and why, and E-08 must implement the status/vocabulary exemption either way, since BOTH precedents agree that a vocabulary question matching nothing is a success.

### OQ-02: Should an unmatched selector make `aw attention --check` fail?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED AT REVIEW (F8), non-blocking because E-10 ships the fail-closed form and the answer changes one branch. `--check` is the CI gate and its current answer is actively false: `aw att zzzzzz --check` prints "the view is valid." and exits 0, asserting validity about a token it never resolved. FOR MAKING IT A VIOLATION: `--check`'s contract is "fail closed on an invalid view", and a view that answers about nothing is not a valid answer; routing it through the drift set gets the CI behavior for free. AGAINST: a `Drift` record is a repository-CONTRACT finding about an artifact, while an unmatched token is an operator input error, so putting it in `violations` conflates "the repo is wrong" with "you typed wrong", and it would flip the `--json` `valid` flag (E-09). Note the CI invocation is unaffected either way: `.github/workflows/tests.yml:145` runs `attention --check --agent` with NO selector, so nothing to mismatch. E-10 must implement the refusal as a SEPARATE condition from drift (per F12's composition requirement) so the maintainer can relax it without touching the drift path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted three-way fixture result at execution HEAD showing (a) a nonexistent selector, (b) a token that MATCHES an artifact removed by a DOWNSTREAM filter, and (c) a matching visible artifact, with the human line counts, the exit codes, and the `--agent` `outcome`/`exit`/`findings` triples side by side, demonstrating that (a) and (b) are currently indistinguishable and (c) differs. State the exact invocation used for (b) and that the artifact was re-derived at execution time rather than taken from this plan. REJECT a fixture that uses a merely-parked artifact for (b): paste the `aw att <parked-id6>` output showing it IS displayed, which is what makes that fixture invalid.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted per-form table derived from an actual read of `filter_items_by_selectors` at execution HEAD (paste the code range or the search), naming every matching rung including the final substring rung, with an explicit statement of which rungs can match WITHOUT the token resolving as an identifier. PLUS one concrete token measured in each direction: one that matches without resolving, and one that resolves but under-matches what the path rung would catch.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the per-token match facts pasted for a matching token, a non-matching token, and a token whose only match is removed by a DOWNSTREAM `-t`/`--status` filter, showing the third reads MATCHED. Assert this through the CLI path as well as the pure function, since the ordering defect (F7) lives in `run()` and a pure-function-only check would pass while the CLI still reported a typo. PLUS proof the filtered list is unchanged: the six existing assertions at `tests/test_attention.py:439-471` pasted green.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted human output for (a) a nonexistent selector naming the token, (b) a two-token invocation where exactly one is unmatched, showing only that one reported, and (c) an all-matching invocation shown byte-identical to today. PLUS the F4 regression guard: a substring selector that resolves as no identifier but matches by path, shown NOT reported as a no-match. PLUS the F7 guard at the CLI level: the downstream-filtered case shown NOT reported as a no-match. State whether `format_empty_result` was reused and, if not, why a second message shape was justified.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `--agent` records for the no-match and the matched-but-empty cases pasted side by side and visibly different, PLUS each shown passing `agent_schema.validate_agent_record` (paste the validation call and its ACTUAL return value, not an assertion that it validates). State how the chosen shape relates to the `aw runs` precedent (`cannot-run`/exit 2/`unresolved_targets`) and justify any divergence. A claim that no valid representation exists is REFUTED in advance by F5's withdrawal and may not be used to skip this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the chosen exit code demonstrated for all three fixture cases AND for a vocabulary token, the pinning test pasted green, and the code comment quoted showing the reasoning, the `25kzda` precedent, AND the rejected alternative are recorded at the decision site. PLUS the drift-composition case (F12): a no-match selector on a drifty view, showing neither code masks the other. If the exit code changed, the updated `--help` exit documentation quoted too.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted eight-surface table with the MEASURED current behavior (output and exit code) per surface at execution HEAD, the decided target behavior, the output channel, and a reason for any surface deliberately left unchanged. A table copied from this plan rather than re-measured does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the vocabulary set printed FROM the contract symbols (paste the code that derives it, not a literal list), each of the five measured zero-match tokens shown under the decided treatment with its exit code, and the `25kzda` Section 2.4a citation quoted. PLUS proof no `attention_contract.py` edit was made (the tree-set gap belongs to `m867ox`): paste `git diff --stat` showing that file untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: the `--json` payload pasted for a no-match and for a matched-but-empty selector, visibly different; the `valid` flag's value in each; the `schema_version` before and after with the bump decision stated; and a statement of what a `/whatnext` run reading the new payload would now conclude for a mistyped selector.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: pasted before/after for `--check`, `-id`, `--paths` and `--filenames` with a nonexistent selector, each showing the message, the CHANNEL it went to (demonstrate by redirecting stdout and stderr separately), and the exit code. For the three list modes, STDOUT proven byte-identical to today. PLUS the bare `python -m agent_workflows attention --check --agent` CI invocation run and shown unchanged. PLUS confirmation that the `--check` refusal is a separate condition from the drift set, per OQ-02.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (10 E-items in 2 task groups, under the 18-leaf / 5-group thresholds). The four items added at review are all narrow: E-07 and E-08 are enumerations feeding E-06, and E-09 and E-10 each cover one already-identified output surface.

EXECUTION CONTRACT. `OQ-01` and `OQ-02` are non-blocking and the maintainer's; execute with the
FAIL-CLOSED form (nonzero on a no-match, `--check` refusing) and do not guess a relaxation. SCOPE FENCE:
this plan declares `agent_workflows/attention.py`, `tests/test_attention.py` and `agent_workflows/cli.py`
(the last for the `--help` exit contract only); an out-of-scope edit must be made only if genuinely
required and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path
left unmodified needs a `--scope-ack`. DO NOT EDIT `agent_workflows/attention_contract.py`: the
tracked-tree gap E-08 will notice is owned by approved plan `m867ox`, which declares that file.

FOUR FACTS MEASURED AT REVIEW THAT YOU MUST NOT RE-DERIVE FROM THE ORIGINAL TEXT, because each one
would send you the wrong way. FIRST, a selector already forces `show_all`, so "matched but hidden" is not
a case; the matched-but-empty twin is a DOWNSTREAM-FILTERED match. SECOND, the match fact CANNOT be
computed inside `filter_items_by_selectors`, because `--type` narrows the list before the call; computing
it there ships the false no-match F4 forbids (F7). THIRD, an honest agent record DOES validate under the
current schema and `aw runs` already ships the shape, so F5's escape hatch is closed and no schema change
is authorized. FOURTH, the exit-code question has an approved-spec precedent (`25kzda` Sections 2.3/2.4a)
plus a live counter-example (`aw find`); cite which you followed.

TWO REGRESSION GUARDS ARE MANDATORY RATHER THAN NICE TO HAVE, because this plan's own subject is a silent
failure and a fix that reports a FALSE no-match is a WORSE defect than the one being fixed: V-04's
substring guard (F4) and V-03/V-04's downstream-filter guard at the CLI level (F7).

THE HARD-MUST HONESTY RULE: paste the ACTUAL command and test output for every `V-*`, never claim a run
not performed, and never present an agent record as schema-valid without pasting the validator's own
return value. RUN THE SUITE BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or
`-p no:randomly`. Commit path-scoped (`git commit -m msg -- <paths>`); never `git add -A`; never push.
Before every commit run `git diff --cached --name-only` and unstage anything not yours; this is a shared
checkout with concurrent sessions, and three other pending plans declare `attention.py`. After the gate,
move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
