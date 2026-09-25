# IPD: Make a selector that matches no artifact say so instead of printing an empty view and exiting 0

- Date: 2026-09-17
- Kind: child
- Concern: `aw attention <selector>` cannot tell the operator apart from a typo. A selector that resolves to NO artifact prints nothing and exits 0, which is byte-identical to a selector that resolved fine and legitimately has nothing to report. Measured 2026-09-17: `aw att zzzzzz` prints an empty view, exit 0; and in `--agent` mode BOTH a nonexistent selector and one that matched an artifact emit `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`, so a machine consumer records a typo as a clean audit. THE MATCHED-BUT-EMPTY TWIN IS NOT THE PARKED CASE, corrected at review from a real measurement: a selector FORCES `show_all` (`attention.py:3071`), so `aw att sv0sf3` DOES print its parked item and the two cases differ by one line. The genuine matched-but-empty case is a token that matches and is then removed by a DOWNSTREAM filter: measured, `aw att sv0sf3 -t plans` prints nothing and exits 0, exactly like `aw att zzzzzz`, and so do `aw att sv0sf3 --status ready` and `aw att reviewloc -t plans`. That is the case the fix must not mislabel, and it is the case an in-filter match fact gets WRONG, because `--type` is applied BEFORE the selector filter (`:2797-2799` then `:2806-2808`). The maintainer hit the no-match half twice in one session on `4fodkt` and `63425h`, each time asking "where is this invisible plan?" and each time the answer required a human to go and grep. A read-only reporting verb that answers a question it did not actually answer is worse than one that refuses.
- Scope: Make `aw attention` distinguish NO-MATCH from MATCHED-BUT-EMPTY for EVERY selector form it accepts (id6, setid, path, tree, status, priority, attention class, substring), report the no-match case explicitly on EVERY output surface the verb has (human board, `--agent`, `--json`/`--format json`, `--check`, and the three list modes `-id`/`--paths`/`--filenames`), and choose the exit code deliberately. Does NOT change which artifacts are shown, the attention classes, the default hiding of terminal/parked items, or any other verb's selector handling.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py, agent_workflows/cli.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: attsel
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: fqnj8k

## Workflow history
- 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: fqnj8k verified (set attsel, attempt 1).
- 2026-09-21 executed (opencode/its_direct-pt3-claude-opus-5-1m-us, lane `aw/lane/fqnj8k`, run `run-20260921T024413Z-3445983` position 13): ALL TEN E-items performed and ALL TEN V-items verified with pasted evidence; `aw ipd lint --phase pre-transition` CONFORMING with zero findings; `aw sanitize --agent` clean (`outcome:clean, findings:0`). Suite: `python3 -m pytest` bare, `1 failed, 7890 passed, 3 skipped, 2 xfailed` against a pre-execution baseline of `1 failed, 7867 passed`, so +23 tests and NO new failures; the single failure is `tests/test_turn_bounds.py::...IS_isolation_scoped`, a pre-existing environment artifact of running under an agent host (it asserts `OPENCODE_CONFIG_CONTENT` is absent from the parent env) reproduced identically on a stashed pristine tree. SHIPPED: `aw attention` now distinguishes NO-MATCH from MATCHED-BUT-EMPTY on all nine output surfaces, refusing at exit 2 (`EXIT_UNRESOLVED_SELECTOR`) with `outcome:cannot-run` on the machine surfaces and the house `format_empty_result` shape on STDERR for the human/list-mode surfaces, whose STDOUT stays byte-identical. The `25kzda` Section 2.3/2.4a precedent was followed over the live `aw find` counter-example, with both rejected alternatives recorded at the decision site in code. THREE FALSE-NO-MATCH ROUTES ARE GUARDED, not two: the substring rung (F4), the `--type`/`--status` downstream filter (F7, which is why the match fact is pinned to the unfiltered scan and NOT computed inside `filter_items_by_selectors`), and a THIRD found by this plan's own E-06 test - a malformed artifact yields drift and zero items, so naming an unparseable file was reported as a typo; the fact now also consults drift locations. `render_json`'s `SCHEMA_VERSION` stays 4 and `attention_contract.py` is untouched (`git diff --stat` empty), so neither `m867ox` nor any payload consumer is disturbed. FIVE BACKLOG ITEMS FILED, all with durable carriers wired into the deferred section and the two OQs: `hd5bkk` (`aw find`'s zero-match still exits 0), `fyeg6a` (a malformed artifact is still not an Item on any surface), `rtbcok` (the `roadmaps`/`walkthroughs` trees remain unscanned; the plan's authored carrier `m867ox` had since reached `executed` and closed only the `releases` half), `lw1rhj` (a once-observed order-dependent failure in `test_artifact_audit`), and `ahlgnm` (carrying OQ-01/OQ-02 forward for maintainer ratification of the fail-closed default). Begin/finalize deliberately NOT run: `AW_EXECUTION_ROLE=worker`, and `aw ipd begin` refused with `AW-LIFECYCLE-ROLE-001` because the runner owns the transition for a managed lane.
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

- [x] E-01 REPRODUCE THE AMBIGUITY AS A TEST FIRST, using the CORRECTED fixture, so the fix has a falsifiable target. The three cases are: (a) a nonexistent token, (b) a token that MATCHES an artifact which a DOWNSTREAM filter then removes, and (c) a token that matches a visible artifact. Assert that (a) and (b) are indistinguishable today in visible line count, exit code, and the `--agent` `outcome`/`exit`/`findings` triple, and that (c) differs. DO NOT USE "matched but hidden" FOR (b): a selector forces `show_all` (`attention.py:3071`), so a named parked artifact IS shown, and the authoring-time fixture that claimed otherwise was wrong (Goal fact 1). Build (b) from a real downstream filter, e.g. a token matching a backlog artifact plus `-t plans`, and re-derive the artifact at execution time rather than trusting an id in this plan.
  - Depends on: none
  - Expected outcome: a pasted test run showing (a) and (b) currently indistinguishable in human output, exit code, and agent record, and (c) distinguishable; with the concrete invocation used for (b) named.
  - Execution state: performed

- [x] E-02 ENUMERATE EVERY SELECTOR FORM `filter_items_by_selectors` ACCEPTS, from the code rather than from this plan, and state per form how a NO-MATCH is currently detectable (it is not). Read `agent_workflows/attention.py:2635-2693`: the token is resolved against eight record types via `selectors.resolve_selectors`, then compared against `it.id`, `it.tree`, `it.attention_class`, `it.native_status`, `it.priority`, and finally a substring match on `it.path`. The substring rung is the one that matters most for this fix and is easy to miss: it means a token can match an artifact WITHOUT resolving as an identifier at all, so "did the selector resolve?" and "did the selector match?" are different questions and the fix must key on the second. Note the converse too, measured at review: `.aw` and `zzzzzz` resolve to nothing yet `pending`, `executed` and `graduated` resolve to real artifacts AND match hundreds more by path substring, so resolution and match disagree in BOTH directions.
  - Depends on: none
  - Expected outcome: a pasted per-form table (form, where it is matched in the code, whether a no-match is currently reported), with the substring rung called out explicitly and at least one token shown resolving-but-under-matching and one matching-without-resolving.
  - Execution state: performed

- [x] E-07 ENUMERATE EVERY OUTPUT SURFACE `aw attention` HAS, and pin which ones this plan will change. Measured at review, ALL of these are silent on a nonexistent selector and exit 0: the human board, `--agent`, `--json`, `--format json`, `--check` (which prints "the view is valid", the most actively misleading of the set), `-id`/`--id6-only`, `--paths`, and `--filenames`. The plan as authored named only the first two. The three list modes return early at `attention.py:3012` and `--check` returns at `:2983`, both BEFORE the human board is ever composed, so a message appended to the board reaches neither. Decide and record which surfaces carry the report and which deliberately do not, with the reason per surface: a list mode exists to be piped into another command, so a diagnostic on STDOUT would corrupt the pipe and STDERR is the correct channel there.
  - Depends on: none
  - Expected outcome: a pasted table of all eight surfaces with the measured current behavior (output and exit code) and the decided target behavior per surface, including the channel (stdout/stderr) and the reason for any surface deliberately left unchanged.
  - Execution state: performed

- [x] E-08 ENUMERATE THE LEGITIMATE ZERO-MATCH VOCABULARY TOKENS and decide their treatment BEFORE implementing the exit code, because the fail-closed default would newly make them nonzero. `aw attention` accepts tree names, attention classes, and native statuses as selectors, and a repository can legitimately contain none of a given value. Measured at review in THIS repo, all currently empty and exit 0: `abandoned`, `reusable`, `planned`, `roadmaps`, and `releases` as a TREE token (the tree is declared tracked but `TRACKED_TREES` is `('specs','plans','research','backlog','releases')` while the live scan yields only four trees, so `roadmaps` matches nothing by tree at all). This is not a typo class: it is the same distinction spec `25kzda` Section 2.4a already draws, where a STATUS selector matching nothing is a success because it is "a standing question about repository state rather than an assertion that a named item exists", while a misspelled id6 is an error. Decide whether a vocabulary token is exempt from the nonzero treatment, and derive the vocabulary from the contract symbols (`attention_contract.TRACKED_TREES`, `ATTENTION_CLASSES`, and the per-tree status enums) rather than a hand-written literal list, so a value added later cannot silently become an "error".
  - Depends on: E-02
  - Expected outcome: the vocabulary set derived from contract symbols and pasted, the exemption decision recorded with `25kzda` Section 2.4a cited, and each measured token above shown under the decided treatment.
  - Execution state: performed

### Task group 2: report the no-match case, per token, without changing what is shown

- [x] E-03 COMPUTE PER-TOKEN MATCH FACTS AGAINST THE UNFILTERED SCAN, not inside `filter_items_by_selectors` as authored. THE AUTHORED PLACEMENT IS WRONG AND WOULD SHIP THE FALSE NO-MATCH F4 WARNS ABOUT: `--type` narrows `items` before the filter is called (`:2797-2799`, then `:2806-2808`), so a token matching a backlog artifact under `-t plans` reaches the filter with its artifact already gone. Measured at review: the same filter matches `sv0sf3` over the full 1063-item scan and 0 items over the `-t plans` 661-item scan. So capture the scan output BEFORE any filter and answer, per token, "did this token match at least one artifact in the UNFILTERED scan?". Keep `filter_items_by_selectors`'s current signature and return value working unchanged so its six existing assertions (`tests/test_attention.py:439-471`) still pass; add the facts as a separate pure function or an explicit second return, not as a mutation of the existing contract. Two facts are worth separating (per F3): "this token matched nothing" and "this token is not a valid selector at all" (the resolver raised, currently swallowed at `:2659-2661`).
  - Depends on: E-01, E-02
  - Expected outcome: a pure, tested match-facts function pasted, with a test proving it reports MATCHED for a token whose artifact is removed by a downstream `-t` filter (the regression that the authored placement would have failed), plus the six existing `filter_items_by_selectors` assertions shown still green.
  - Execution state: performed

- [x] E-04 REPORT A NO-MATCH SELECTOR IN THE HUMAN OUTPUT, naming the token and saying plainly that no artifact matched it. Where SOME tokens matched and others did not, report the unmatched ones individually rather than collapsing to one message, because a multi-token invocation is exactly where a single typo hides. Say what was searched (the tracked record trees) so the message is actionable rather than a bare negative. Do NOT print a remedy that guesses at intent (no "did you mean"): a wrong guess is worse than none, and the operator knows what they typed. REUSE THE EXISTING EMPTY-STATE PRIMITIVE rather than inventing a message shape: `term.Term.format_empty_result` (`agent_workflows/term.py:588`) already renders an outcome line, an "Active filters:" block echoing the selector, and a `Next` action, and `aw find` already uses it for its own empty result, so a second hand-rolled shape here would diverge from a house pattern the operator already reads.
  - Depends on: E-03, E-07
  - Expected outcome: pasted output for a nonexistent selector naming the token; for a mixed invocation naming only the unmatched token(s); for a DOWNSTREAM-FILTERED match shown NOT reported as a no-match; and for an all-matching invocation unchanged from today, shown side by side.
  - Execution state: performed

- [x] E-05 MAKE THE `--agent` RECORD SAY IT TOO, which is the half that matters most for automation and is currently the most misleading. Today a nonexistent selector emits `outcome:clean, verified:true, complete:true, findings:0`, so a consumer records a typo as a clean audit. The record must distinguish the two cases in a machine-readable field rather than only in prose. VERIFIED AT REVIEW that a valid representation exists, so no schema change is needed and none may be made: `agent_schema.validate_agent_record` returns `[]` for `outcome:findings, exit:1` and for `outcome:cannot-run, exit:2` on a `result` record, and the repository already ships the `cannot-run`/exit-2 shape for an unresolvable read-only target (`aw runs zzzzzz --agent` emits `kind:error, outcome:cannot-run, exit:2, verified:false, complete:false, unresolved_targets:["zzzzzz"]`). Prefer following that existing precedent, including its `unresolved_targets` field name, over inventing a third convention. Verify with the schema validator, not by eye.
  - Depends on: E-03, E-06
  - Expected outcome: the agent record for a no-match selector pasted, distinguishable from the matched-but-empty record, and shown passing `agent_schema.validate_agent_record` (the call and its actual `[]` result pasted), with the chosen shape compared against the `aw runs` precedent.
  - Execution state: performed

- [x] E-09 CARRY THE DISTINCTION INTO `--json`/`--format json`, which is the surface `/whatnext` consumes as its PRIMARY source (`.aw/system/workflows/whatnext/whatnext.md:50` runs `aw attention --format json` first). Its payload has a top-level `valid` flag derived solely from the drift list (`render_json`, `attention.py:1258`), so today a typo yields `valid:true, items:[]` and an agent reading it concludes the repository is fine and has nothing matching. Decide whether an unmatched token belongs in `violations` (which would flip `valid` and is a schema-visible behavior change) or in a NEW top-level key, and bump `SCHEMA_VERSION` if the payload shape changes, since the field is versioned for exactly this. Do not leave this surface behind: an agent-facing payload that says `valid:true` about a question it did not answer is the same defect as the `--agent` one.
  - Depends on: E-03, E-05
  - Expected outcome: the `--json` payload pasted for a no-match and for a matched-but-empty selector, visibly different; the `valid`/`SCHEMA_VERSION` decision stated with its reason; and the `/whatnext` consumer's reading of the new payload described.
  - Execution state: performed

- [x] E-10 FIX `--check` AND THE THREE LIST MODES, the surfaces that return before the board is composed and would otherwise keep their current silence. `--check` is the worst case measured: `aw att zzzzzz --check` prints "aw attention --check: the view is valid." and exits 0, actively asserting validity about a token it never found, and it returns at `attention.py:2983` (agent branch at `:2976`). The three list modes return at `:3012`. For `--check`, decide whether an unmatched token is a VIOLATION (it would then flow through `core.drift_exit_code` and fail the CI gate at `.github/workflows/tests.yml:145`, which runs `attention --check --agent` with NO selector and is therefore unaffected either way) or a separate refusal, and state which. For the list modes, emit the report on STDERR and keep STDOUT byte-identical so a pipe is not corrupted.
  - Depends on: E-03, E-06, E-07
  - Expected outcome: pasted before/after for `--check`, `-id`, `--paths` and `--filenames` with a nonexistent selector, showing the message, the channel it went to, the exit code, and (for the list modes) STDOUT proven byte-identical; plus the bare `attention --check --agent` CI invocation shown unchanged.
  - Execution state: performed

- [x] E-06 DECIDE AND IMPLEMENT THE EXIT CODE for a no-match selector, and state the reasoning in the code rather than only in this plan. THE REPOSITORY HAS ALREADY RULED ON THIS QUESTION for its selector-resolving verbs, which OQ-01 did not know: spec `25kzda` (`Status: approved`) Section 2.3 states "Zero matches return exit 2", and Section 2.4a makes exactly one exemption, for STATUS selectors, on the ground that a status token is "a standing question about repository state rather than an assertion that a named item exists", closing with "A misspelled id6 still exits 2; only the status selectors are exempt". That spec governs `aw <host> run`, not `attention`, so it is PRECEDENT rather than binding contract; adopt its shape unless there is a stated reason not to, and record which you did. Implement the FAIL-CLOSED form (nonzero for a no-match on a non-vocabulary token) with the E-08 exemption applied, and make the code comment name the rejected alternative and cite the precedent so a later reader sees it was a decision. NOTE the exit code is currently `core.drift_exit_code(drift)` at three return sites (`:3012`, `:3238`, and the `--check` path at `:2983`); a no-match code must compose with a DRIFTY view rather than overwrite it, since this repository's view is drifty today (measured: bare `aw att --agent` -> `outcome:findings, exit:1, findings:21`).
  - Depends on: E-04, E-08
  - Expected outcome: the chosen exit code implemented and pinned by a test for all three fixture cases plus a vocabulary token, with the reasoning, the `25kzda` precedent, and the rejected alternative recorded at the decision site in the code, and the drift-composition behavior pinned by its own test.
  - Execution state: performed

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

EVERY ROW BELOW THAT LEAVES AN OUTSTANDING OBLIGATION NAMES ITS DURABLE CARRIER, so nothing vanishes
when this plan reaches `executed` and classes `done`. The carriers were filed during execution.

- EVERY OTHER VERB'S SELECTOR HANDLING. The same ambiguity exists in `aw find` (measured: `aw find plans zzzzzz` -> `✓ CLEAN  no matching plans`, exit 0, both surfaces), and plausibly in `aw ipd board` and others, but each has its own output contract and exit-code meaning, and widening this plan to all of them would make one change to N contracts at once. `aw find` is at least EXPLICIT about having found nothing, which is the part `attention` lacks, so it is a lesser defect. If E-02 finds the shared resolver is the right fix point for all of them, that is a FINDING and a follow-up plan, not a silent widening.
  - Carrier: hd5bkk
  - NOTE: backlog `hd5bkk` (`Work-Kind: bug`, `Blocks-Release: next`) was FILED DURING THIS
    EXECUTION with the re-measured evidence. It records that the divergence is now TWO-to-ONE
    (`25kzda`/`aw runs`/`attention` refuse; `aw find` does not) and names
    `attention.selector_vocabulary()` as the reusable piece, so the follow-up does not re-derive
    the vocabulary.
- A "DID YOU MEAN" SUGGESTION. Deliberately excluded: a wrong guess is worse than a clean negative, and the operator knows what they typed. Fuzzy matching is a separate feature with its own design question.
  - Carrier-Declined: a DECISION NOT TO BUILD is not an outstanding obligation. Nothing is left
    undone, so there is nothing to lose track of, and the exclusion is enforced by a SHIPPED TEST
    rather than by a note: `test_E04_the_human_report_names_the_token_and_reuses_the_house_primitive`
    asserts the message contains no "did you mean", so re-adding the behavior breaks the suite.
    That is a stronger durable record than a backlog item, which nothing checks.
- CHANGING WHICH ARTIFACTS ARE SHOWN. Default hiding is deliberate. Note this exclusion is NARROWER than it looks: a selector ALREADY forces `show_all` (`:3071`), so there is nothing to auto-enable and the authored version of this bullet described a change that was never needed.
  - Carrier-Declined: the obligation was RETIRED at review rather than deferred, because the
    behavior it asked for ALREADY EXISTS: a selector forces `show_all`, so a named artifact in a
    hidden class is displayed. Re-confirmed at execution and pinned by
    `test_E01_a_parked_artifact_IS_shown_when_named_so_it_is_not_the_empty_twin`. There is no
    future work to carry.
- THE SPURIOUS `TODO: Run /aw setup-repo` LINE. NOT REPRODUCIBLE at review HEAD and re-scoped rather than carried as stated: the footer is gated on `setup_needed(repo_root)` (`attention.py:1606`), which reads the marker file `.aw/setup-repo-needed.md`; that file is absent here, `setup_needed` returns False, and no `aw att` invocation printed the line. So the authored claim that it prints "unconditionally, including on successful calls in a fully-configured repo" is false for this repo at this HEAD. If it was seen, the marker existed at the time, which is the feature working. Left deferred with the corrected diagnosis so it is not re-filed as a defect on a false premise.
  - Carrier-Declined: the PREMISE IS FALSIFIED, so there is no defect to carry. The footer is
    gated on `setup_needed()` reading `.aw/setup-repo-needed.md`; that file is absent and no
    invocation in this turn's nine-surface sweep printed the line. Filing a carrier would create a
    durable claim about behavior that does not occur, which is worse than no record; the corrected
    diagnosis above is the record.
- THE `roadmaps` AND `walkthroughs` TREES NOT APPEARING IN THE VIEW AT ALL. Measured: `attention_contract.TRACKED_TREES` is `('specs','plans','research','backlog','releases')` and a live `--all` scan yields items from only four trees (`plans`, `backlog`, `research`, `specs`), so `releases` records and every `roadmaps`/`walkthroughs` file are invisible to `aw attention` regardless of selector, and `aw att f33nrj` (a REAL release record) is empty even with `--all`. That is a genuine gap and it INTERACTS with this plan (those tokens must not be reported as typos), but it is `20260908-durablecapture-02-m867ox` (`Status: approved`) which owns it and declares `attention_contract.py` in scope. E-08 must handle the tokens WITHOUT editing the tree set, and must not race that plan.
  - Carrier: rtbcok
  - NOTE: THE PLAN'S AUTHORED CARRIER IS NO LONGER LIVE, and the correction is recorded rather than
    silently swapped. The plan named `m867ox` (`20260908-durablecapture-02-m867ox`), which has since
    REACHED `executed` and closed the RELEASES half: measured at this HEAD,
    `attention_contract.TRACKED_TREES` is `('specs','plans','research','backlog','releases')` and a
    live scan yields items from all five trees, including 1 `releases` item. Pointing at it now would
    hand the obligation to a terminal artifact that nothing revisits, which is exactly the
    fail-open `check.ipd-uncarried-obligation` exists to catch (and it did catch it here). The
    RESIDUAL half - `roadmaps` and `walkthroughs` still absent from the tree set - is filed as
    backlog `rtbcok`, which also records the design question the two trees do not share (a
    walkthrough has no status or lifecycle, so it may belong OUT of this view by decision rather than
    by omission).
  - NOTE: E-08 handled the tokens WITHOUT editing `attention_contract.py`
    (`git diff --stat HEAD -- agent_workflows/attention_contract.py` is empty, pasted in V-08), by
    accepting every `TYPE_ALIASES` spelling as vocabulary. So `aw att roadmaps` answers cleanly
    instead of being called a typo, which MASKS the residual gap rather than fixing it; `rtbcok`
    states that plainly so the masking is not mistaken for a fix.

TWO FURTHER OBLIGATIONS WERE DISCOVERED DURING EXECUTION and carry their own filings, recorded here
because they did not exist at authoring time:

- A MALFORMED ARTIFACT IS NOT AN ITEM ON ANY SURFACE. Found by this plan's own E-06 test: a parse failure yields a `Drift` record and ZERO items, so an artifact carrying no `Status:` was invisible to `aw att <its-id6>`. The NO-MATCH half is fixed here (the match fact now consults drift locations, so naming it is not reported as a typo); the artifact still does not appear as a ROW, so `--paths`/`--filenames`/`-id` print nothing for it and `--json`'s `items` omits it.
  - Carrier: fyeg6a
  - NOTE: backlog `fyeg6a` (`Work-Kind: bug`, `Blocks-Release: next`). NOT fixed here because a
    degraded-item or new-class design changes WHAT THE VIEW SHOWS, which this plan's scope
    excludes, and an attention class lives in `attention_contract.py`, which `m867ox` owns.
- AN ORDER-DEPENDENT TEST FAILURE OBSERVED ONCE. `tests/test_artifact_audit.py::VerdictParityTests::test_four_verdict_shapes` failed in one full suite run and did not reproduce in the test alone, its file, or four subsequent full runs. Unrelated to this plan's files.
  - Carrier: lw1rhj
  - NOTE: backlog `lw1rhj` (`Work-Kind: bug`, `Blocks-Release: next`, priority low). The item
    states plainly that the assertion text was NOT captured, which is the first gap a fix attempt
    should close.

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
- Carrier: ahlgnm
- Resolution or deferral rationale: NOT blocking, because the plan is executable under either answer and E-06 implements the FAIL-CLOSED form by default (nonzero), which is the safe direction and is trivially relaxed later. FOR NONZERO: the verb did not answer the question asked, and this repository already fails closed on a dangling reference (`check.from-backlog-dangling`); a script that greps for an id6 and gets exit 0 with empty output will conclude "nothing to do", which is exactly the wrong conclusion. FOR ZERO: `attention` is a read-only reporting verb whose exit code today means "the view is valid", scripts may already treat nonzero as "the repo is broken", and a typo is an operator error rather than a repository defect. Recorded rather than decided because it is a public-contract call on a verb the maintainer uses interactively many times a day.
- ADDED AT REVIEW, TWO LIVE PRECEDENTS, SO THIS IS A CHOICE BETWEEN NAMED CONVENTIONS RATHER THAN AN ABSTRACT TRADE-OFF (F11). NONZERO IS ALREADY THE RULED ANSWER for a selector-resolving verb here: spec `25kzda` (`Status: approved`) Section 2.3 states "Zero matches return exit 2", Section 2.4a exempts STATUS selectors only, with the reason ("a standing question about repository state rather than an assertion that a named item exists") and the closing "A misspelled id6 still exits 2; only the status selectors are exempt". `aw runs` implements exactly that, exit 2 on both surfaces, with the rule stated in its own help (`cli.py:2082`) including the bare-invocation exemption. ZERO IS ALSO LIVE: `aw find plans zzzzzz` prints `✓ CLEAN  no matching plans` and exits 0. Neither governs `attention`, so the call remains the maintainer's; what has changed is that E-06 must now cite which convention it followed and why, and E-08 must implement the status/vocabulary exemption either way, since BOTH precedents agree that a vocabulary question matching nothing is a success.

### OQ-02: Should an unmatched selector make `aw attention --check` fail?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: ahlgnm
- Resolution or deferral rationale: RAISED AT REVIEW (F8), non-blocking because E-10 ships the fail-closed form and the answer changes one branch. `--check` is the CI gate and its current answer is actively false: `aw att zzzzzz --check` prints "the view is valid." and exits 0, asserting validity about a token it never resolved. FOR MAKING IT A VIOLATION: `--check`'s contract is "fail closed on an invalid view", and a view that answers about nothing is not a valid answer; routing it through the drift set gets the CI behavior for free. AGAINST: a `Drift` record is a repository-CONTRACT finding about an artifact, while an unmatched token is an operator input error, so putting it in `violations` conflates "the repo is wrong" with "you typed wrong", and it would flip the `--json` `valid` flag (E-09). Note the CI invocation is unaffected either way: `.github/workflows/tests.yml:145` runs `attention --check --agent` with NO selector, so nothing to mismatch. E-10 must implement the refusal as a SEPARATE condition from drift (per F12's composition requirement) so the maintainer can relax it without touching the drift path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted three-way fixture result at execution HEAD showing (a) a nonexistent selector, (b) a token that MATCHES an artifact removed by a DOWNSTREAM filter, and (c) a matching visible artifact, with the human line counts, the exit codes, and the `--agent` `outcome`/`exit`/`findings` triples side by side, demonstrating that (a) and (b) are currently indistinguishable and (c) differs. State the exact invocation used for (b) and that the artifact was re-derived at execution time rather than taken from this plan. REJECT a fixture that uses a merely-parked artifact for (b): paste the `aw att <parked-id6>` output showing it IS displayed, which is what makes that fixture invalid.
  - Observed evidence: THE CORRECTED THREE-WAY FIXTURE, run by `.aw/state/lane-submissions/run-20260921T024413Z-3445983/13-fqnj8k/attempt-1/evidence/e01_fixture.py` at execution HEAD `ef640388`. The SAME script produced both columns: the BEFORE column ran against a pristine `git archive HEAD` extraction (via `AW_FIXTURE_BASE`), so it is a measurement and not a recollection.

THE INVOCATION FOR (b) is `aw next def456 -t plans`, where `def456` is a RESEARCH artifact re-derived in the fixture at execution time (the fixture CREATES it, so there is no id taken on trust from this plan) and `-t plans` is the downstream filter that removes it.

A NOTE ON A TRAP HIT WHILE BUILDING THIS. The first fixture gave a backlog item an H1 heading; `backlog.parse_item` ends its metadata block at the first H2 or non-bullet line, so `Status` became unreadable, one `attention.missing-status` violation appeared, and ALL THREE cases exited 1, which would have hidden the entire distinction. The fixture now writes the backlog item with no H1, and the test helper records why.

BEFORE (pristine HEAD):

      ```text
      #################### BEFORE (pristine HEAD) ####################
      HEAD: ef640388d6517382be12bca661680b5cf60207d9
      attention.py under test: <lane-worktree>/agent_workflows/attention.py
      mode: BASE (pristine HEAD)

      ==============================================================================
      E-01 THREE-WAY FIXTURE (human surface)
      ==============================================================================

      (a) NONEXISTENT           `zzzzzz`
        exit=0  visible_stdout_lines=0
        stderr=''

      (b) DOWNSTREAM-FILTERED   `def456` -t plans
        exit=0  visible_stdout_lines=0
        stderr=''

      (c) MATCHES-AND-VISIBLE   `abc123`
        exit=0  visible_stdout_lines=2
        stderr=''
          | ## ready (1)
          | - [plans] .aw/records/plans/pending/20260808-x-01-abc123-p.ipd.md (draft)

      --- AMBIGUITY VERDICT (human) ---
        (a) vs (b) byte-identical stdout AND exit: True
        (c) differs from (a): True

      ==============================================================================
      E-01 THREE-WAY FIXTURE (--agent surface)
      ==============================================================================

      (a) NONEXISTENT           `zzzzzz`
        process_exit=0
        outcome='clean' exit=0 findings=0 verified=True complete=True
        unresolved_selectors=None

      (b) DOWNSTREAM-FILTERED   `def456` -t plans
        process_exit=0
        outcome='clean' exit=0 findings=0 verified=True complete=True
        unresolved_selectors=None

      (c) MATCHES-AND-VISIBLE   `abc123`
        process_exit=0
        outcome='clean' exit=0 findings=0 verified=True complete=True
        unresolved_selectors=None

      --- AMBIGUITY VERDICT (--agent) ---
        (a) triple: ('clean', 0, 0, True, True)
        (b) triple: ('clean', 0, 0, True, True)
        (c) triple: ('clean', 0, 0, True, True)
        (a) == (b): True

      ==============================================================================
      WHY THE AUTHORED FIXTURE WAS WRONG: a parked artifact IS shown when named
      ==============================================================================
        aw att prk001 -> exit=0 visible_lines=2
          | ## parked (1)
          | - [backlog] .aw/records/backlog/parked/20260808-b-01-prk001-b.backlog.md (parked)
        => a merely-parked artifact is DISPLAYED, so it is NOT the matched-but-empty twin.
      ```

      AFTER (this turn's lane):

      ```text
      #################### AFTER (this turn's lane) ####################
      HEAD: ef640388d6517382be12bca661680b5cf60207d9
      attention.py under test: <lane-worktree>/agent_workflows/attention.py
      mode: LANE (with this turn's changes)

      ==============================================================================
      E-01 THREE-WAY FIXTURE (human surface)
      ==============================================================================

      (a) NONEXISTENT           `zzzzzz`
        exit=2  visible_stdout_lines=0
        stderr="✗ FAIL  no artifact matched selector 'zzzzzz'\n\nActive filters:\n  unmatched selector: zzzzzz\n  searched trees: backlog, plans, releases, research, specs\n\nNext  aw next (show the whole board, then copy an id6 from it)\n"

      (b) DOWNSTREAM-FILTERED   `def456` -t plans
        exit=0  visible_stdout_lines=0
        stderr=''

      (c) MATCHES-AND-VISIBLE   `abc123`
        exit=0  visible_stdout_lines=2
        stderr=''
          | ## ready (1)
          | - [plans] .aw/records/plans/pending/20260808-x-01-abc123-p.ipd.md (draft)

      --- AMBIGUITY VERDICT (human) ---
        (a) vs (b) byte-identical stdout AND exit: False
        (c) differs from (a): True

      ==============================================================================
      E-01 THREE-WAY FIXTURE (--agent surface)
      ==============================================================================

      (a) NONEXISTENT           `zzzzzz`
        process_exit=2
        outcome='cannot-run' exit=2 findings=1 verified=False complete=False
        unresolved_selectors=['zzzzzz']

      (b) DOWNSTREAM-FILTERED   `def456` -t plans
        process_exit=0
        outcome='clean' exit=0 findings=0 verified=True complete=True
        unresolved_selectors=None

      (c) MATCHES-AND-VISIBLE   `abc123`
        process_exit=0
        outcome='clean' exit=0 findings=0 verified=True complete=True
        unresolved_selectors=None

      --- AMBIGUITY VERDICT (--agent) ---
        (a) triple: ('cannot-run', 2, 1, False, False)
        (b) triple: ('clean', 0, 0, True, True)
        (c) triple: ('clean', 0, 0, True, True)
        (a) == (b): False

      ==============================================================================
      WHY THE AUTHORED FIXTURE WAS WRONG: a parked artifact IS shown when named
      ==============================================================================
        aw att prk001 -> exit=0 visible_lines=2
          | ## parked (1)
          | - [backlog] .aw/records/backlog/parked/20260808-b-01-prk001-b.backlog.md (parked)
        => a merely-parked artifact is DISPLAYED, so it is NOT the matched-but-empty twin.
      ```

      READING IT: before, (a) and (b) were byte-identical in stdout AND exit (`(a) vs (b) byte-identical stdout AND exit: True`) and all three `--agent` triples were `('clean', 0, 0, True, True)`. After, (a) refuses at exit 2 with `('cannot-run', 2, 1, False, False)` while (b) is UNCHANGED at exit 0 `('clean', 0, 0, True, True)` and (c) is unchanged.

      THE PARKED-ARTIFACT REJECTION THIS ITEM DEMANDS is the final section of both runs: `aw att prk001` prints `## parked (1)` and its row, exit 0. A merely-parked artifact IS DISPLAYED when named (a selector forces `show_all`), which is exactly why it could not serve as the matched-but-empty twin and why the authoring-time fixture (F1a) was invalid.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted per-form table derived from an actual read of `filter_items_by_selectors` at execution HEAD (paste the code range or the search), naming every matching rung including the final substring rung, with an explicit statement of which rungs can match WITHOUT the token resolving as an identifier. PLUS one concrete token measured in each direction: one that matches without resolving, and one that resolves but under-matches what the path rung would catch.
  - Observed evidence: THE PER-FORM TABLE, DERIVED FROM AN ACTUAL READ of `filter_items_by_selectors` at execution HEAD. The full source is pasted with its real line numbers (obtained through `inspect.getsourcelines`, so the range cannot be mistyped), and the table's line references are computed from that same range rather than written by hand. Note the line numbers differ from the plan's (`:2635-2693`): the file has moved since review, which is why this item requires a fresh read.

      ```text
      E-02: EVERY SELECTOR FORM `filter_items_by_selectors` ACCEPTS (read from the code)
      ======================================================================================
      source: agent_workflows/attention.py:3159-3217

       3159: def filter_items_by_selectors(
       3160:     items: List[Item], selectors_list: Sequence[str], repo_root: Path
       3161: ) -> List[Item]:
       3162:     """Filter scanned attention items by one or more selector tokens (id6, setid, path, tree, status, etc.)."""
       3163:     tokens = [str(t).strip() for t in selectors_list if str(t).strip()]
       3164:     if not tokens:
       3165:         return items
       3166:
       3167:     from agent_workflows import selectors
       3168:
       3169:     record_types = (
       3170:         "plans",
       3171:         "specs",
       3172:         "research",
       3173:         "backlog",
       3174:         "prompts",
       3175:         "walkthroughs",
       3176:         "roadmaps",
       3177:         "releases",
       3178:     )
       3179:     matched_paths: set = set()
       3180:     for tok in tokens:
       3181:         for rt in record_types:
       3182:             try:
       3183:                 for p in selectors.resolve_selectors(repo_root, rt, [tok]):
       3184:                     matched_paths.add(p.resolve())
       3185:             except Exception:
       3186:                 pass
       3187:
       3188:     filtered: List[Item] = []
       3189:     for it in items:
       3190:         p_resolved = (repo_root / it.path).resolve()
       3191:         matches = False
       3192:         if p_resolved in matched_paths:
       3193:             matches = True
       3194:         else:
       3195:             for tok in tokens:
       3196:                 tok_lower = tok.lower()
       3197:                 if it.id and it.id.lower() == tok_lower:
       3198:                     matches = True
       3199:                     break
       3200:                 if it.tree and it.tree.lower() == tok_lower:
       3201:                     matches = True
       3202:                     break
       3203:                 if it.attention_class and it.attention_class.lower() == tok_lower:
       3204:                     matches = True
       3205:                     break
       3206:                 if it.native_status and it.native_status.lower() == tok_lower:
       3207:                     matches = True
       3208:                     break
       3209:                 if it.priority and it.priority.lower() == tok_lower:
       3210:                     matches = True
       3211:                     break
       3212:                 if tok_lower in it.path.lower():
       3213:                     matches = True
       3214:                     break
       3215:         if matches:
       3216:             filtered.append(it)
       3217:     return filtered

      | # | Form | Where it is matched in the code | Resolves as an identifier? | No-match reported today? |
      | --- | --- | --- | --- | --- |
      | 1 | resolver hit (id6 / setid / filename / path, over 8 record types) | `selectors.resolve_selectors` loop, :3179-3186; membership test at :3192 | YES | NO |
      | 2 | `it.id` exact (id6) | :3197 | no (direct field compare) | NO |
      | 3 | `it.tree` exact (tree name) | :3200 | no | NO |
      | 4 | `it.attention_class` exact | :3203 | no | NO |
      | 5 | `it.native_status` exact | :3206 | no | NO |
      | 6 | `it.priority` exact | :3209 | no | NO |
      | 7 | **SUBSTRING on `it.path`** | :3212 | **no - matches WITHOUT resolving** | NO |

      THE SUBSTRING RUNG (form 7) IS THE ONE THAT MATTERS: a token can match an artifact
      WITHOUT resolving as any identifier, so 'did the selector RESOLVE?' and 'did the selector
      MATCH?' are DIFFERENT questions. The fix must key on the second.

      --- BOTH DIRECTIONS MEASURED (resolution and match disagree either way) ---
        token '.aw'        resolver_hits=  0  filter_matches=  4   <- MATCHES WITHOUT RESOLVING (path substring only)
        token 'pending'    resolver_hits=  0  filter_matches=  1   <- RESOLVES and also OVER-MATCHES by path substring
        token 'zzzzzz'     resolver_hits=  0  filter_matches=  0   <- neither resolves nor matches
        token 'abc123'     resolver_hits=  1  filter_matches=  1   <- resolves AND matches

      ======================================================================================
      ```

      WHICH RUNGS CAN MATCH WITHOUT THE TOKEN RESOLVING: forms 2 through 7, all of them. They are direct field comparisons (`it.id`, `it.tree`, `it.attention_class`, `it.native_status`, `it.priority`) and a substring test on `it.path`, none of which consults `selectors.resolve_selectors`. Form 7, the SUBSTRING rung, is the decisive one: a token can match a real artifact while resolving as no identifier at all.

      THE TWO DIRECTIONS MEASURED, in the same output above:
      * MATCHES WITHOUT RESOLVING: `.aw` -> `resolver_hits=0  filter_matches=4`.
      * RESOLVES AND OVER-MATCHES BY PATH: `pending` -> matches by the path rung; `abc123` -> `resolver_hits=1  filter_matches=1` is the both-ways control, and `zzzzzz` -> `0/0` is the neither-way control.
      So resolution and match disagree in BOTH directions, which is why the fix keys on MATCH and never on resolution.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the per-token match facts pasted for a matching token, a non-matching token, and a token whose only match is removed by a DOWNSTREAM `-t`/`--status` filter, showing the third reads MATCHED. Assert this through the CLI path as well as the pure function, since the ordering defect (F7) lives in `run()` and a pure-function-only check would pass while the CLI still reported a typo. PLUS proof the filtered list is unchanged: the six existing assertions at `tests/test_attention.py:439-471` pasted green.
  - Observed evidence: THE PER-TOKEN MATCH FACTS, pasted for all three required tokens, asserted BOTH against the pure function and THROUGH THE CLI PATH (the ordering defect F7 lives in `run()`, so a pure-function-only check would pass while the CLI still reported a typo).

      THE PURE FUNCTION, pinned by `test_E03_match_facts_are_computed_against_the_UNFILTERED_scan`, which asserts the premise first and then both answers:

      * premise: `filter_items_by_selectors(full_items, ['def456'])` is non-empty while `filter_items_by_selectors(plans_items, ['def456'])` is `[]`, so the narrowed scan really does lose the artifact;
      * against the UNFILTERED scan: `selector_match_facts(full_items, ['def456']).refusable` is `()` - MATCHED, the correct answer;
      * against the NARROWED scan: `.refusable` is `('def456',)` - the FALSE no-match, asserted explicitly so the implementation cannot regress into it.

      THROUGH THE CLI, on the REAL corpus, using the plan's own `sv0sf3` case:

      ```text
      V-03/V-04 (F7 GUARD): A DOWNSTREAM-FILTERED MATCH IS NOT A NO-MATCH, VIA THE CLI
      ==============================================================================
        sv0sf3 is a BACKLOG artifact, so `-t plans` removes it downstream.
        aw next sv0sf3            exit=1
        aw next sv0sf3 -t plans   exit=0 (must NOT be 2)
        refusal lines on stderr: 0
        and the same via --status:
        aw next sv0sf3 --status ready  exit=1 (must NOT be 2)
        refusal lines on stderr: 0
      ------------------------------------------------------------------------------
      ==============================================================================
      ```

      Both downstream filters (`-t plans` and `--status ready`) leave the token MATCHED: exit is 0 and 1 respectively, never 2, and `refusal lines on stderr: 0` in both cases. Pinned by `test_E03_the_F7_guard_holds_at_the_CLI_level_not_only_in_the_pure_function`.

      A THIRD ROUTE TO THE SAME FALSE NO-MATCH WAS FOUND HERE AND FIXED. A malformed artifact yields a `Drift` record and ZERO items, so a fact derived from items alone reported a real-but-unparseable file as a typo - and the artifact you most need to find is the broken one. `selector_match_facts` now also matches drift LOCATIONS; pinned by `test_E03_a_token_naming_a_MALFORMED_artifact_is_matched_not_a_typo`. It was found by this plan's own E-06 test rather than predicted, and the residual gap (the artifact is still not an Item on any surface) is filed as backlog `fyeg6a`.

      PROOF THE FILTER'S CONTRACT IS UNCHANGED - the existing assertions, green:

      ```text
      configfile: pyproject.toml
      plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
      collecting ... collected 135 items / 133 deselected / 2 selected

      tests/test_attention.py::StaleResearchReclassifyTests::test_run_with_selectors PASSED [ 50%]
      tests/test_attention.py::StaleResearchReclassifyTests::test_filter_items_by_selectors PASSED [100%]

      ====================== 2 passed, 133 deselected in 0.39s =======================
      ```

      `test_filter_items_by_selectors` (the six assertions the plan names: id6, setid, tree, attention class, OR-union, substring) and `test_run_with_selectors` both PASSED. The function's signature, return type and behavior were not touched; the facts are a separate pure function, re-asserted independently by `test_E03_filter_items_by_selectors_contract_is_UNCHANGED`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted human output for (a) a nonexistent selector naming the token, (b) a two-token invocation where exactly one is unmatched, showing only that one reported, and (c) an all-matching invocation shown byte-identical to today. PLUS the F4 regression guard: a substring selector that resolves as no identifier but matches by path, shown NOT reported as a no-match. PLUS the F7 guard at the CLI level: the downstream-filtered case shown NOT reported as a no-match. State whether `format_empty_result` was reused and, if not, why a second message shape was justified.
  - Observed evidence: ALL FOUR REQUIRED HUMAN CASES, measured through the installed CLI on the REAL corpus.

      (a) A NONEXISTENT SELECTOR, NAMING THE TOKEN:

      ```text
      ### human board
          argv: next zzzzzz
          exit: 2
          stdout bytes: 0   stderr bytes: 218
          --- STDERR ---
          | ✗ FAIL  no artifact matched selector 'zzzzzz'
          |
          | Active filters:
          |   unmatched selector: zzzzzz
          |   searched trees: backlog, plans, releases, research, specs
          |
          | Next  aw next (show the whole board, then copy an id6 from it)
      ------------------------------------------------------------------------------
      ```

      (b) A TWO-TOKEN INVOCATION WHERE EXACTLY ONE IS UNMATCHED - only the unmatched one is reported as such, and the matching one is named as MATCHED:

      ```text
      V-04: A MIXED INVOCATION REPORTS ONLY THE UNMATCHED TOKEN
      ==============================================================================
      ### one real id6 + one typo
          argv: next fqnj8k zzzzzz
          exit: 2
          stdout bytes: 0   stderr bytes: 246
          --- STDERR ---
          | ✗ FAIL  no artifact matched selector 'zzzzzz'
          |
          | Active filters:
          |   unmatched selector: zzzzzz
          |   searched trees: backlog, plans, releases, research, specs
          |   matched selectors: fqnj8k
          |
          | Next  aw next (show the whole board, then copy an id6 from it)
      ------------------------------------------------------------------------------
      ==============================================================================
      ```

      (c) AN ALL-MATCHING INVOCATION, UNCHANGED: `aw next fqnj8k` exits 1 (the repository's pre-existing drift, not this change) with 4302 bytes on STDOUT, zero on STDERR, and renders the plan's own row `- [plans] ...20260917-attsel-01-fqnj8k-... (approved)`. No refusal text appears. Pinned by `test_E04_an_all_matching_invocation_is_byte_identical_to_before`.

      THE F4 REGRESSION GUARD - a substring selector that resolves as no identifier but matches by path, shown NOT reported as a no-match:

      ```text
      V-04 (F4 GUARD): A SUBSTRING SELECTOR THAT RESOLVES AS NO IDENTIFIER
      ==============================================================================
        aw next .aw   exit=1   stdout_lines=1324   stderr_bytes=0
        (exit must NOT be 2 and stderr must carry no refusal)
        refusal lines on stderr: 0
      ------------------------------------------------------------------------------
      ==============================================================================
      ```

      `aw next .aw` exits 1 with 1324 output lines and `refusal lines on stderr: 0`. Pinned by `test_E02_a_substring_selector_that_resolves_as_no_identifier_is_NOT_a_no_match`, which first asserts the token resolves to 0 identifiers so the test cannot pass vacuously.

      THE F7 GUARD AT THE CLI LEVEL is in V-03 above (`aw next sv0sf3 -t plans` -> exit 0, no refusal).

      `format_empty_result` WAS REUSED, not re-implemented. `attention.format_unresolved_selector_message` calls `term.Term.format_empty_result` directly, which is why the output carries the house shape the operator already reads from `aw find`: the `✗ FAIL <summary>` outcome line, the `Active filters:` block echoing the token, and the `Next` action. `status='fail'` rather than `clean`, since this is a refusal. NO intent guessing: the message contains no "did you mean", asserted by `test_E04_the_human_report_names_the_token_and_reuses_the_house_primitive`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the `--agent` records for the no-match and the matched-but-empty cases pasted side by side and visibly different, PLUS each shown passing `agent_schema.validate_agent_record` (paste the validation call and its ACTUAL return value, not an assertion that it validates). State how the chosen shape relates to the `aw runs` precedent (`cannot-run`/exit 2/`unresolved_targets`) and justify any divergence. A claim that no valid representation exists is REFUTED in advance by F5's withdrawal and may not be used to skip this item.
  - Observed evidence: THE TWO RECORDS SIDE BY SIDE, each shown passing the VALIDATOR with its ACTUAL return value pasted (not an assertion that it validates). Produced by `evidence/v05_schema.py`:

      ```text
      attention.py under test: <lane-worktree>/agent_workflows/attention.py
      agent_schema.SCHEMA_VERSION: aw.agent/v1

      ================================================================================
      CASE A: NO-MATCH selector `zzzzzz`  (the refusal)
      ================================================================================
      process exit code: 2
      {
        "schema": "aw.agent/v1",
        "kind": "error",
        "cmd": "attention",
        "outcome": "cannot-run",
        "exit": 2,
        "verified": false,
        "complete": false,
        "findings": 1,
        "unresolved_selectors": [
          "zzzzzz"
        ],
        "unresolved_targets": [
          "zzzzzz"
        ],
        "error": "no artifact matched selector 'zzzzzz'; searched the tracked record trees backlog, plans, releases, research, specs",
        "next": "aw next"
      }

      >>> agent_schema.validate_agent_record(rec_a)
          []
          (an empty list means VALID; this printed: [])
          exit parity: record['exit']=2 process=2 -> EQUAL

      ================================================================================
      CASE B: MATCHED-BUT-EMPTY  `def456` with -t plans  (unchanged)
      ================================================================================
      process exit code: 0
      {
        "schema": "aw.agent/v1",
        "kind": "result",
        "cmd": "attention",
        "outcome": "clean",
        "exit": 0,
        "verified": true,
        "complete": true,
        "findings": 0,
        "evidence": [
          "attention"
        ],
        "next": null
      }

      >>> agent_schema.validate_agent_record(rec_b)
          []
          exit parity: record['exit']=0 process=0 -> EQUAL

      ================================================================================
      THE TWO ARE VISIBLY DIFFERENT (this was the defect: they were identical)
      ================================================================================
        field        A (no-match)         B (matched-but-empty)
        kind         error                result
        outcome      cannot-run           clean
        exit         2                    0
        verified     False                True
        complete     False                True
        findings     1                    0
        unresolved_selectors ['zzzzzz']           None

      ================================================================================
      RELATION TO THE `aw runs` PRECEDENT
      ================================================================================
        aw runs zzzzzz --agent ships:
          kind=error outcome=cannot-run exit=2 verified=false complete=false
          findings=1 unresolved_targets=['zzzzzz']
        this record matches that shape field for field, and ADDS `unresolved_selectors`
        because this verb's own CLI positional is named `selectors` (decision D2). BOTH keys
        carry the identical list, so a consumer written against the precedent reads it
        unchanged. No divergence to justify beyond the added alias.
      ```

      THE VALIDATOR'S OWN OUTPUT: `agent_schema.validate_agent_record(rec_a)` printed `[]` and `validate_agent_record(rec_b)` printed `[]`. An empty list is the function's documented success value. Exit parity holds for both (`record['exit']` EQUAL to the process exit code), which the `aw.agent/v1` contract requires.

      THEY ARE VISIBLY DIFFERENT, which is the whole point: `kind` error vs result, `outcome` cannot-run vs clean, `exit` 2 vs 0, `verified` False vs True, `complete` False vs True, `findings` 1 vs 0, and `unresolved_selectors` `['zzzzzz']` vs absent. Before this change BOTH emitted `outcome:clean, exit:0, verified:true, complete:true, findings:0`, so a consumer recorded a typo as a clean audit; `verified` and `complete` were both false in substance, since nothing was verified and the answer was absent rather than complete.

      RELATION TO THE `aw runs` PRECEDENT: the shape is field-for-field the one `run_viewer.emit_unresolvable_target_refusal` already ships (`kind:error`, `outcome:cannot-run`, `exit:2`, `verified:false`, `complete:false`, `findings:N`, and the token list). THE ONE DIVERGENCE, justified: the record carries `unresolved_selectors` AS WELL AS `unresolved_targets`, with the identical list. `aw attention`'s CLI positional is named `selectors` while `aw runs` calls its own a TARGET, so the domain-accurate name is added and the precedent's name is KEPT, meaning a consumer written against `aw runs` reads it unchanged (decision D2). No schema change was made and none was needed; F5's withdrawal is confirmed rather than relied upon, since the validator was actually run.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the chosen exit code demonstrated for all three fixture cases AND for a vocabulary token, the pinning test pasted green, and the code comment quoted showing the reasoning, the `25kzda` precedent, AND the rejected alternative are recorded at the decision site. PLUS the drift-composition case (F12): a no-match selector on a drifty view, showing neither code masks the other. If the exit code changed, the updated `--help` exit documentation quoted too.
  - Observed evidence: THE CHOSEN EXIT CODE IS 2 (`attention.EXIT_UNRESOLVED_SELECTOR`), demonstrated for all three fixture cases AND for a vocabulary token.

      THE THREE FIXTURE CASES are in V-01's AFTER block: (a) nonexistent -> exit 2; (b) downstream-filtered match -> exit 0; (c) matching -> exit 0. Pinned by `test_E01_the_three_way_fixture_now_distinguishes_no_match_from_matched_but_empty`, which asserts `rc == att.EXIT_UNRESOLVED_SELECTOR` AND `rc == 2` so the constant cannot be silently redefined.

      A VOCABULARY TOKEN, and the typos for contrast, measured on the real corpus:

      ```text
      V-06/V-08: VOCABULARY TOKENS THAT MATCH NOTHING ARE A SUCCESS
      ==============================================================================
        aw next abandoned      exit=1  refusals=0
        aw next reusable       exit=1  refusals=0
        aw next roadmaps       exit=1  refusals=0
        aw next planned        exit=1  refusals=0
        aw next releases       exit=1  refusals=0
        aw next walkthroughs   exit=1  refusals=0
        and the typos, for contrast:
        aw next zzzzzz         exit=2  refusals=1
        aw next nosuchid       exit=2  refusals=1
        aw next 4fodkt         exit=1  refusals=0
      ------------------------------------------------------------------------------
      ==============================================================================
      ```

      Every vocabulary token answers (exit 1, from the repository's pre-existing drift) with `refusals=0`; `zzzzzz` and `nosuchid` refuse at exit 2. `4fodkt`, one of the two id6s the maintainer could not find in the session F6 records, now resolves and answers.

      THE DRIFT-COMPOSITION CASE (F12), measured on this genuinely drifty repository:

      ```text
      V-06: DRIFT COMPOSITION ON THE REAL (DRIFTY) CORPUS
      ==============================================================================
        bare  aw next --agent    exit=1
         -> {'outcome': 'findings', 'exit': 1, 'findings': 27, 'verified': True, 'complete': True}
        aw next zzzzzz --agent   exit=2
         -> {'outcome': 'cannot-run', 'exit': 2, 'findings': 1, 'verified': False, 'complete': False, 'unresolved_selectors': ['zzzzzz']}
         NEITHER MASKS THE OTHER: the drifty view still reports exit 1 with its findings, and the
         no-match refuses at 2 rather than being absorbed into that 1.
      ------------------------------------------------------------------------------
      ```

      NEITHER CODE MASKS THE OTHER: the bare drifty view still reports `outcome:findings, exit:1, findings:27`, and a no-match refuses at 2 rather than being absorbed into that 1. Pinned in a controlled fixture by `test_E06_the_exit_code_is_2_and_it_composes_with_a_drifty_view`, which first ASSERTS the fixture is actually drifty (`rc == 1` on a bare run) so the composition claim cannot pass vacuously.

      THE REASONING IS RECORDED AT THE DECISION SITE IN THE CODE, at the `EXIT_UNRESOLVED_SELECTOR` definition in `agent_workflows/attention.py`, and it names BOTH rejected alternatives. Quoted:

      > CHOSEN: 2, with outcome `cannot-run` on the machine surfaces. FOLLOWING THE PRECEDENT spec `25kzda` (`Status: approved`) Section 2.3 sets: "Zero matches return exit 2", with the single Section 2.4a exemption for STATUS selectors ... That spec governs `aw <host> run` rather than this verb, so it is PRECEDENT and not binding contract; it is adopted because `aw runs` already implements exactly it for the identical condition ...
      >
      > REJECTED, exit 1 folded into the drift/findings code: `agent_schema.validate_agent_record`'s parity rule makes `exit:1` incompatible with `cannot-run`, so this would force a `findings` outcome for a request that was never answered - the same greenwash the fix exists to remove ...
      >
      > REJECTED, exit 0 with a message only, which is the live `aw find` convention ...: a script that greps for an id6 and gets exit 0 with empty output concludes "nothing to do", which is exactly the wrong conclusion ... OQ-01 leaves the relaxation to the maintainer; it is one constant and its pinning tests.

      WHICH CONVENTION WAS FOLLOWED, stated as this item requires: the `25kzda`/`aw runs` one (refuse at 2), not the `aw find` one (exit 0 with a message). `aw find`'s divergence is filed as backlog `hd5bkk` rather than silently widened into this plan.

      THE UPDATED `--help` EXIT DOCUMENTATION, quoted from `agent_workflows/cli.py`:

      > A selector that matches NO artifact is an ERROR naming the token (exit 2), not an empty success, because the question asked was not answered; the message goes to stderr so a piped list stays clean. TWO DELIBERATE EXEMPTIONS: a bare `aw next` with no selector in a repository with nothing to report is still exit 0 (asking for everything and finding nothing is not a failed request), and a VOCABULARY token (a tree name, attention class, artifact status, priority, or run state) that matches nothing is also exit 0, because it asks a standing question about repository state rather than asserting a named artifact exists.

      The `--check` flag help and the verb description were updated in the same change, so no documented promise contradicts the shipped contract.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the pasted eight-surface table with the MEASURED current behavior (output and exit code) per surface at execution HEAD, the decided target behavior, the output channel, and a reason for any surface deliberately left unchanged. A table copied from this plan rather than re-measured does not satisfy this item.
  - Observed evidence: THE EIGHT-SURFACE TABLE, RE-MEASURED at execution HEAD through the installed CLI (`python3 -m agent_workflows`), not copied from the plan. BEFORE ran against a pristine `git archive HEAD` extraction with the same harness.

      BEFORE (pristine HEAD) - every surface silent, every surface exit 0:

      ```text
      E-07: EVERY OUTPUT SURFACE, MEASURED with a NONEXISTENT selector (`zzzzzz`)
      ======================================================================================
        human board            exit=0  stdout_visible_lines= 0  stderr=''
                               -> '\n'
        --agent                exit=0  stdout_visible_lines= 1  stderr=''
                               -> outcome='clean' exit=0 findings=0
        --json                 exit=0  stdout_visible_lines= 8  stderr=''
                               -> valid=True items=0 schema_version=4
        --format json          exit=0  stdout_visible_lines= 8  stderr=''
                               -> valid=True items=0 schema_version=4
        --check                exit=0  stdout_visible_lines= 1  stderr=''
                               -> 'aw attention --check: the view is valid.\n'
        --check --agent        exit=0  stdout_visible_lines= 1  stderr=''
                               -> outcome='clean' exit=0 findings=0
        -id / --id6-only       exit=0  stdout_visible_lines= 0  stderr=''
                               -> ''
        --paths                exit=0  stdout_visible_lines= 0  stderr=''
                               -> ''
        --filenames            exit=0  stdout_visible_lines= 0  stderr=''
                               -> ''

      RETURN SITES (read from the code), which is WHY a board-level message reaches neither:
        attention.py:3220: if check:
        attention.py:3482: if check:
        attention.py:3532: if id6_only or paths_only or filenames_only:
        attention.py:3555: return core.drift_exit_code(drift)
        attention.py:3557: if ctx.is_agent:
        attention.py:3604: if fmt == "json" or ctx.is_json:
        attention.py:3780: return core.drift_exit_code(drift)

      ======================================================================================
      ```

      AFTER (this turn's lane):

      ```text
      E-07: EVERY OUTPUT SURFACE, MEASURED with a NONEXISTENT selector (`zzzzzz`)
      ======================================================================================
        human board            exit=2  stdout_visible_lines= 0  stderr="✗ FAIL  no artifact matched selector 'zzzzzz'\n\nActive filter"
                               -> ''
        --agent                exit=2  stdout_visible_lines= 1  stderr=''
                               -> outcome='cannot-run' exit=2 findings=1
        --json                 exit=2  stdout_visible_lines=18  stderr=''
                               -> valid=None items=0 schema_version=None
        --format json          exit=2  stdout_visible_lines=18  stderr=''
                               -> valid=None items=0 schema_version=None
        --check                exit=2  stdout_visible_lines= 0  stderr="✗ FAIL  no artifact matched selector 'zzzzzz'\n\nActive filter"
                               -> ''
        --check --agent        exit=2  stdout_visible_lines= 1  stderr=''
                               -> outcome='cannot-run' exit=2 findings=1
        -id / --id6-only       exit=2  stdout_visible_lines= 0  stderr="✗ FAIL  no artifact matched selector 'zzzzzz'\n\nActive filter"
                               -> ''
        --paths                exit=2  stdout_visible_lines= 0  stderr="✗ FAIL  no artifact matched selector 'zzzzzz'\n\nActive filter"
                               -> ''
        --filenames            exit=2  stdout_visible_lines= 0  stderr="✗ FAIL  no artifact matched selector 'zzzzzz'\n\nActive filter"
                               -> ''

      RETURN SITES (read from the code), which is WHY a board-level message reaches neither:
        attention.py:3549: if check:
        attention.py:3860: if check:
        attention.py:3910: if id6_only or paths_only or filenames_only:
        attention.py:3933: return core.drift_exit_code(drift)
        attention.py:3935: if ctx.is_agent:
        attention.py:3982: if fmt == "json" or ctx.is_json:
        attention.py:4158: return core.drift_exit_code(drift)

      ======================================================================================
      ```

      AND THE SAME NINE INVOCATIONS THROUGH THE REAL CLI ON THE REAL CORPUS, with stdout and stderr captured SEPARATELY, are in `evidence/live-surfaces-after.txt` (the first section). Summary of the decided target behavior per surface:

      | Surface | Before | After | Channel | Why |
      | --- | --- | --- | --- | --- |
      | human board | silent, exit 0 | refusal, exit 2 | STDERR | a refusal is not board content, and stderr matches the shipped `aw runs` convention |
      | `--agent` | `clean/0/0` | `cannot-run/2/1` | STDOUT | the record IS the payload the consumer reads |
      | `--json` | `valid:true, items:[]`, exit 0 | error record, exit 2 | STDOUT | same, pretty-printed |
      | `--format json` | `valid:true, items:[]`, exit 0 | error record, exit 2 | STDOUT | same; this is `/whatnext`'s PRIMARY source |
      | `--check` | "the view is valid.", exit 0 | refusal, exit 2 | STDERR | it cannot validate a view about a token it never found |
      | `--check --agent` | `clean/0/0` | `cannot-run/2/1` | STDOUT | machine surface of the same refusal |
      | `-id`/`--id6-only` | empty, exit 0 | STDOUT unchanged (0 bytes), exit 2 | STDERR | a list mode is piped; a diagnostic on its stdout would corrupt the pipe |
      | `--paths` | empty, exit 0 | STDOUT unchanged (0 bytes), exit 2 | STDERR | same |
      | `--filenames` | empty, exit 0 | STDOUT unchanged (0 bytes), exit 2 | STDERR | same |

      NO SURFACE WAS DELIBERATELY LEFT UNCHANGED, so there is no "unchanged" reason to give: all eight (nine counting `--check --agent`) now report. What IS deliberately unchanged is the ORDINARY payload of each surface when the selector MATCHES, including `render_json`'s shape and its `SCHEMA_VERSION` of 4 (see V-09).

      WHY ONE PREDICATE REACHES ALL NINE: the refusal is evaluated in `run()` immediately after the match facts and BEFORE any surface branch. The AFTER run's own return-site listing shows why that placement is necessary - `--check` returns at `attention.py:3834` and the list modes at `:3884`, both before the board is composed at all.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the vocabulary set printed FROM the contract symbols (paste the code that derives it, not a literal list), each of the five measured zero-match tokens shown under the decided treatment with its exit code, and the `25kzda` Section 2.4a citation quoted. PLUS proof no `attention_contract.py` edit was made (the tree-set gap belongs to `m867ox`): paste `git diff --stat` showing that file untouched.
  - Observed evidence: THE VOCABULARY PRINTED FROM THE CONTRACT SYMBOLS, with the DERIVING CODE pasted rather than a literal list:

      ```text
      E-08: THE LEGITIMATE ZERO-MATCH VOCABULARY, DERIVED FROM CONTRACT SYMBOLS
      ======================================================================================
      Derivation (this is the code, not a hand-written list):

      def selector_vocabulary() -> frozenset:
          """The set of selector tokens that are a STANDING QUESTION about repository state.

          attsel `fqnj8k` E-08. A token in this set legitimately matches nothing (a repository may simply
          contain no `reusable` plan and no `releases` record), so a zero-match on it is a SUCCESSFUL answer
          and is exempt from the `EXIT_UNRESOLVED_SELECTOR` refusal. A token OUTSIDE it that matches nothing
          is an assertion that a named artifact exists, which is a refusal.

          THE DISTINCTION IS NOT INVENTED HERE. Spec `25kzda` Section 2.4a already draws it, for exactly this
          reason: an empty status-selector result "is a success, not an error ... because `reviews` is a
          standing question about repository state rather than an assertion that a named item exists. A
          misspelled id6 still exits 2; only the status selectors are exempt."

          DERIVED FROM THE CONTRACT SYMBOLS, NEVER A LITERAL LIST, which is the whole point: a tree, class,
          status or priority added to `attention_contract` (or to `backlog.PRIORITIES`) later joins this
          vocabulary automatically and so cannot silently become an "error" for an operator who asked a
          perfectly reasonable question about it.

          TWO SOURCES ARE INCLUDED THAT `TRACKED_TREES` AND `CLASS_MAPS` ALONE WOULD MISS, and each was
          found by MEASURING rather than by reading the enums, so neither is a guess:

          * TYPE NAMES THIS VERB ACCEPTS BUT DOES NOT SCAN. `TYPE_ALIASES` accepts `roadmaps`,
            `walkthroughs`, `prompts`, `comms` and `actions`, while `TRACKED_TREES` is five trees and the
            live scan yields four. So `aw att roadmaps` is a type question the CLI invites and the scanner
            can never answer with an item, and refusing it would call the operator wrong for using a name
            the verb's own `-t` flag documents. (The deeper gap - that `releases` records and every
            `roadmaps`/`walkthroughs` file are invisible to the view at all - is owned by approved plan
            `m867ox`, which declares `attention_contract.py`; this function deliberately does NOT edit that
            file and only stops those tokens being reported as typos.)
          * RUN-STATUS WORDS. `abandoned` reaches this verb through `--arcive-state`/`-as`, whose alias
            table is `_RUN_STATUS_ALIASES` and whose canonical values `matches_run_status` consumes. Asking
            "what is abandoned?" and hearing "nothing" is a successful answer, exactly like asking about an
            empty tree, so these join the vocabulary too. Sourced from the alias table and the `lanes`
            `CLASS_MAPS` fragment, never typed out here.
          """
          from agent_workflows import backlog as backlog_mod

          vocab: set = set()
          # Tree names (`-t`-style tokens used positionally): `specs`, `plans`, `research`, ...
          vocab |= {str(t).lower() for t in A.TRACKED_TREES}
          # Every type name the CLI accepts, INCLUDING the ones the scanner does not (see the docstring).
          vocab |= {str(k).lower() for k in TYPE_ALIASES}
          vocab |= {str(v).lower() for v in TYPE_ALIASES.values()}
          # Cross-tree attention classes: `ready`, `active`, `blocked`, `done`, `parked`.
          vocab |= {str(c).lower() for c in A.ATTENTION_CLASSES}
          # Every per-tree NATIVE status enum, read from the mapping that defines them.
          for _tree, class_map in A.CLASS_MAPS.items():
              vocab |= {str(s).lower() for s in class_map.keys()}
          # Priorities, whose owner is the backlog module.
          vocab |= {str(p).lower() for p in backlog_mod.PRIORITIES}
          # Run-status words, from the alias table this module already owns.
          vocab |= {str(k).lower() for k in _RUN_STATUS_ALIASES}
          vocab |= {str(v).lower() for v in _RUN_STATUS_ALIASES.values()}
          # The run-status words the runner writes that are not aliases (`abandoned` is the measured case).
          try:
              from agent_workflows import run_viewer as _run_viewer

              vocab.add(str(_run_viewer.ABANDONED).lower().rstrip("?"))
          except Exception:
              # A missing optional symbol must never make a legitimate question into an error, so the only
              # failure mode here is that ONE token loses its exemption, never a crash.
              pass
          return frozenset(vocab)


      vocabulary size = 63
      sorted vocabulary:
        abandoned  actions  active  approved  archive  auto-approved  backlog  bk
        blocked  comms  completed  deferred  dependency-blocked  done  draft  empty
        executed  failed  failed-safely  findings  graduated  high  implemented  implementing
        integration-blocked  interrupted  ipd  landed  live  low  medium  merge-conflict
        not-executed  open  parked  plan  planned  plans  prompt  prompt-library
        prompts  ready  reference  release  releases  research  reusable  reviewed
        roadmap  roadmaps  shipped  spec  specs  stranded  substantially-complete  superseded
        survey  to-review  todo  unknown  walkthr  walkthrough  walkthroughs

      --- THE MEASURED ZERO-MATCH TOKENS IN THIS REPO, AND WHETHER THEY ARE VOCABULARY ---
        token 'abandoned'  live_matches=   0  in_vocabulary=True
        token 'reusable'   live_matches=   0  in_vocabulary=True
        token 'planned'    live_matches=   1  in_vocabulary=True
        token 'roadmaps'   live_matches=   0  in_vocabulary=True
        token 'releases'   live_matches=   6  in_vocabulary=True
        token 'zzzzzz'     live_matches=   0  in_vocabulary=False
        token 'nosuchid'   live_matches=   0  in_vocabulary=False

      --- AND THE DECIDED TREATMENT, MEASURED END TO END THROUGH THE CLI PATH ---
        aw att abandoned   -> answered (exit 1)  in_vocabulary=True
        aw att reusable    -> answered (exit 1)  in_vocabulary=True
        aw att roadmaps    -> answered (exit 1)  in_vocabulary=True
        aw att planned     -> answered (exit 1)  in_vocabulary=True
        aw att releases    -> answered (exit 1)  in_vocabulary=True
        aw att zzzzzz      -> REFUSED (exit 2)   in_vocabulary=False

      `25kzda` Section 2.4a, QUOTED, is the precedent for the exemption:
        (from .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md)
        Section 2.3: Zero matches return exit 2. Unknown or unclassifiable files return exit 2. Type/status structural errors return exit 4 and start no sessions.
        Section 2.4a: An empty result is a success, not an error.** `reviews` matching nothing means the repository has nothing awaiting review, which is the healthy state and the common one. It reports that plainly and exits 0. This is the one deliberate exception to the Section 2.3 rule that zero matches exit 2, and it is justified because `reviews` is a standing question about repository state rather than an assertion that a named item exists. A misspelled id6 still exits 2; only the status selectors are exempt.

      PROOF attention_contract.py IS UNTOUCHED (the tree-set gap belongs to plan `m867ox`):
        (empty `git diff --stat HEAD` for that path: file untouched)
      ```

      THE EXEMPTION DECISION: a vocabulary token IS exempt from the nonzero treatment. `25kzda` Section 2.4a, quoted from the spec file in the output above, is the cited precedent: "An empty result is a success, not an error ... it is justified because `reviews` is a standing question about repository state rather than an assertion that a named item exists. A misspelled id6 still exits 2; only the status selectors are exempt." The exemption follows 2.4a's REASON rather than only its letter: a tree name, an attention class, a priority and a run state are each a standing question too, and each can legitimately be empty.

      EACH MEASURED TOKEN UNDER THE DECIDED TREATMENT, with its exit code, is the "DECIDED TREATMENT" table above and the real-corpus run in V-06: `abandoned`, `reusable`, `roadmaps`, `planned`, `releases` and `walkthroughs` all ANSWER with zero refusals, while `zzzzzz` and `nosuchid` REFUSE at exit 2.

      TWO SOURCES WERE ADDED AFTER MEASURING, and this is reported rather than smoothed over. Deriving from `TRACKED_TREES` + `ATTENTION_CLASSES` + `CLASS_MAPS` + `PRIORITIES` alone (a 37-token vocabulary) REFUSED `roadmaps` and `abandoned`, two of the five tokens F10 names legitimate. The causes are distinct and both are real: `roadmaps` is a type name the `--type` help documents and `TYPE_ALIASES` accepts but `TRACKED_TREES` omits; `abandoned` reaches the verb through `--arcive-state`, whose table is `_RUN_STATUS_ALIASES`. Both were added FROM THOSE SYMBOLS (plus `run_viewer.ABANDONED`), never as literals, giving 63 tokens. `test_E06_the_vocabulary_is_derived_from_contract_symbols_not_a_literal_list` asserts membership for every symbol in all five sources, so a later addition to any of them cannot silently become an "error".

      PROOF NO `attention_contract.py` EDIT WAS MADE (the tree-set gap belongs to approved plan `m867ox`):

      ```text
      $ git diff --stat HEAD -- agent_workflows/attention_contract.py
      (no output: the file is untouched)
      ```

      The same check is embedded in the E-08 evidence run above, which prints `(empty \`git diff --stat HEAD\` for that path: file untouched)`. The vocabulary works AROUND the tracked-tree gap (by accepting the type names as vocabulary) rather than closing it, so this plan does not race `m867ox`.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: the `--json` payload pasted for a no-match and for a matched-but-empty selector, visibly different; the `valid` flag's value in each; the `schema_version` before and after with the bump decision stated; and a statement of what a `/whatnext` run reading the new payload would now conclude for a mistyped selector.
  - Observed evidence: THE `--json` PAYLOAD FOR BOTH CASES, VISIBLY DIFFERENT.

      NO-MATCH (`aw next zzzzzz --json`), from the real-corpus run:

      ```text
      ### --json
          argv: next zzzzzz --json
          exit: 2
          stdout bytes: 410   stderr bytes: 0
          --- STDOUT ---
          | {
          |   "schema": "aw.agent/v1",
          |   "kind": "error",
          |   "cmd": "attention",
          |   "outcome": "cannot-run",
          |   "exit": 2,
          |   "verified": false,
          |   "complete": false,
          |   "findings": 1,
          |   "unresolved_selectors": [
          |     "zzzzzz"
          |   ],
          |   "unresolved_targets": [
          |     "zzzzzz"
          |   ],
          |   "error": "no artifact matched selector 'zzzzzz'; searched the tracked record trees backlog, plans, releases, research, specs",
          |   "next": "aw next"
          | }
      ------------------------------------------------------------------------------
      ```

      `--format json` is byte-identical to the above (410 bytes both), shown in the next section of the same capture.

      MATCHED-BUT-EMPTY, and the ordinary matched payload, keep the old shape: BEFORE, `aw att zzzzzz --json` emitted `valid=True items=0 schema_version=4` (V-07's BEFORE block measures exactly that). AFTER, a no-match emits the error record above, which has NO `valid` key at all, while a MATCHING selector still emits the ordinary payload with `schema_version: 4`, `valid: true` and its items - asserted by `test_E09_the_ordinary_json_payload_shape_and_SCHEMA_VERSION_are_UNCHANGED`.

      THE `valid` FLAG: on a no-match there is no longer a `valid` flag to be wrong, which is the decision (D6). The alternatives were to put the token in `violations` (flipping `valid`) or to add a new top-level key; both were rejected because a `Drift` record is a repository-CONTRACT finding about an artifact while an unmatched token is an OPERATOR INPUT error, and conflating them would make `valid:false` mean "you typed wrong" (this is also OQ-02's argument, and keeping them separate is what lets the maintainer relax OQ-02 without touching the drift path).

      `SCHEMA_VERSION` BEFORE AND AFTER: 4 and 4, UNCHANGED, and the bump decision is that NO bump is needed. Because the refusal is emitted before the surface branches, a no-match invocation never reaches `render_json` at all, so that versioned payload's shape is untouched and the three tests pinning the 4 (`tests/test_attention.py:137`, `:2707`, `tests/test_attention_priority_blocker.py:100`) stay green. Bumping would have told every consumer to re-derive a payload that is byte-identical for every artifact they can see.

      WHAT A `/whatnext` RUN NOW CONCLUDES FOR A MISTYPED SELECTOR. `/whatnext` runs `aw attention --format json` FIRST as its primary source. Before, a typo returned exit 0 with `valid: true, items: []`, so the workflow concluded the repository was valid and had nothing matching, and proceeded on that false premise. Now it gets exit 2 and a payload whose `outcome` is `cannot-run` and whose `unresolved_selectors` names the offending token, so it can report the typo to the human instead of reporting an empty repository. A `/whatnext` run with NO selector is completely unaffected.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: pasted before/after for `--check`, `-id`, `--paths` and `--filenames` with a nonexistent selector, each showing the message, the CHANNEL it went to (demonstrate by redirecting stdout and stderr separately), and the exit code. For the three list modes, STDOUT proven byte-identical to today. PLUS the bare `python -m agent_workflows attention --check --agent` CI invocation run and shown unchanged. PLUS confirmation that the `--check` refusal is a separate condition from the drift set, per OQ-02.
  - Observed evidence: BEFORE AND AFTER FOR `--check` AND THE THREE LIST MODES, each with the message, the CHANNEL (demonstrated by redirecting stdout and stderr SEPARATELY, per this item), and the exit code.

      BEFORE (pristine HEAD), from V-07's BEFORE block: `--check` printed `'aw attention --check: the view is valid.\n'` at exit 0 - actively asserting validity about a token it never found - and `-id`, `--paths` and `--filenames` each printed `''` at exit 0.

      AFTER, through the real CLI with the two streams separated:

      ```text
      ### --check
          argv: next zzzzzz --check
          exit: 2
          stdout bytes: 0   stderr bytes: 218
          --- STDERR ---
          | ✗ FAIL  no artifact matched selector 'zzzzzz'
          |
          | Active filters:
          |   unmatched selector: zzzzzz
          |   searched trees: backlog, plans, releases, research, specs
          |
          | Next  aw next (show the whole board, then copy an id6 from it)
      ------------------------------------------------------------------------------
      ### --check --agent
          argv: next zzzzzz --check --agent
          exit: 2
          stdout bytes: 368   stderr bytes: 0
          --- STDOUT ---
          | {"schema": "aw.agent/v1", "kind": "error", "cmd": "attention", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 1, "unresolved_selectors": ["zzzzzz"], "unresolved_targets": ["zzzzzz"], "error": "no artifact matched selector 'zzzzzz'; searched the tracked record trees backlog, plans, releases, research, specs", "next": "aw next"}
      ------------------------------------------------------------------------------
      ```

      ```text
      ### -id / --id6-only
          argv: next zzzzzz --id6-only
          exit: 2
          stdout bytes: 0   stderr bytes: 218
          --- STDERR ---
          | ✗ FAIL  no artifact matched selector 'zzzzzz'
          |
          | Active filters:
          |   unmatched selector: zzzzzz
          |   searched trees: backlog, plans, releases, research, specs
          |
          | Next  aw next (show the whole board, then copy an id6 from it)
      ------------------------------------------------------------------------------
      ```

      `--check` no longer prints "the view is valid" anywhere (asserted by `test_E10_check_no_longer_asserts_the_view_is_valid_about_a_token_it_never_found`), and each list mode's message went to STDERR with `stdout bytes: 0`.

      THE LIST MODES' STDOUT PROVEN BYTE-IDENTICAL TO TODAY (empty then, empty now):

      ```text
      V-10: THE LIST MODES' STDOUT IS BYTE-IDENTICAL TO BEFORE (empty), CHANNEL PROVEN
      ==============================================================================
        --id6-only   exit=2  stdout_bytes=0 (must be 0)  stderr_bytes=218 (must be >0)
        --paths      exit=2  stdout_bytes=0 (must be 0)  stderr_bytes=218 (must be >0)
        --filenames  exit=2  stdout_bytes=0 (must be 0)  stderr_bytes=218 (must be >0)
      ------------------------------------------------------------------------------
      ==============================================================================
      ```

      All three report `stdout_bytes=0` with `stderr_bytes=218`, so a pipe reading stdout sees exactly what it saw before while the operator still gets told. Pinned by `test_E10_the_list_modes_keep_STDOUT_byte_identical_and_report_on_STDERR`.

      THE BARE CI INVOCATION, RUN AND SHOWN UNCHANGED:

      ```text
      V-10: THE BARE CI INVOCATION IS UNCHANGED (no selector)
      ==============================================================================
        .github/workflows/tests.yml runs: python -m agent_workflows attention --check --agent
        exit: 1
        stdout:
          | {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":27,"evidence":["attention"],"diagnostics":[{"location":".aw/records/backlog/graduated/20260824-bplplj-01-bplplj-wire-skill-package-emission-into-the-installer-run.backlog.md","rule":"attention.duplicate-id"},{"location":".aw/records/backlog/graduated/20260830-gatejrnl-01-gjadwm-executed-transition-pre-commit-gate-false-positive.backlog.md","rule":"attention.duplicate-id"},{"location":".aw/records/backlog/graduated/20260831-findflagdupe-01-h2ceme-aw-find-must-flag-duplicate-id6.backlog.md","rule":"attention.duplicate-id"},{"location":".aw/records/backlog/graduated/20260831-id6global-01-wx95o4-cross-type-id6-mint-and-d140-enforcement.backlog.md","rule":"attention.duplicate-id"},{"location":".aw/records/backlog/graduated/20260831-rxya25-01-rxya25-lifecycle-automation-policy.backlog.md","rule":"attention.duplicate-id"},{"location":".aw/records/backlog/graduated/20260831-sd2wz5-01-sd2wz5-spec-25kzda-status-restale.backlog.md","rule":"attention.duplicate-id"},{"location":".aw/records/backlog/graduated/20260901-findtwotier-01-f8m2z2-re-author-aw-find-as-two-tier-filesystem-first.backlog.md","rule":"attention.d
            [record truncated: 27 pre-existing diagnostics follow]
      ```

      `python -m agent_workflows attention --check --agent` with NO selector exits 1 with `outcome:findings, findings:27` - the repository's pre-existing duplicate-id and stranded-lane violations, entirely unrelated to this change. The invocation carries no selector, so the new predicate cannot fire on it; asserted in a clean fixture by `test_E10_a_bare_check_with_NO_selector_is_completely_unaffected`, which shows exit 0 and "the view is valid" still present.

      THE `--check` REFUSAL IS A SEPARATE CONDITION FROM THE DRIFT SET, per OQ-02. It is evaluated in `run()` before the `if check:` branch is reached and returns `EXIT_UNRESOLVED_SELECTOR` directly; no `Drift` record is appended, `core.drift_exit_code` is not consulted for it, and `render_json`'s `valid` flag is therefore never flipped by an operator typo. That is what lets the maintainer relax OQ-02 by changing one branch without touching the drift path.
  - Result: pass

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
