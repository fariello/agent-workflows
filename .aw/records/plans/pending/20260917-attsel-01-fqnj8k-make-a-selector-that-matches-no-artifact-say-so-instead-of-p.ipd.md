# IPD: Make a selector that matches no artifact say so instead of printing an empty view and exiting 0

- Date: 2026-09-17
- Kind: child
- Concern: `aw attention <selector>` cannot tell the operator apart from a typo. A selector that resolves to NO artifact prints nothing and exits 0, which is byte-identical to a selector that resolved fine and legitimately has nothing to report. Measured 2026-09-17: `aw att zzzzzz` prints an empty view, exit 0; `aw att sv0sf3` (a REAL parked backlog item) also prints one line and exits 0; and in `--agent` mode BOTH emit `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`, so a machine consumer records a typo as a clean audit. The maintainer hit this twice in one session on `4fodkt` and `63425h`, each time asking "where is this invisible plan?" and each time the answer required a human to go and grep. A read-only reporting verb that answers a question it did not actually answer is worse than one that refuses.
- Scope: Make `aw attention` distinguish NO-MATCH from MATCHED-BUT-EMPTY for EVERY selector form it accepts (id6, setid, path, tree, status, priority, attention class, substring), report the no-match case explicitly in both human and `--agent` output, and choose the exit code deliberately. Does NOT change which artifacts are shown, the attention classes, the default hiding of terminal/parked items, or any other verb's selector handling.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py
- Item-Dependencies: none
- Status: to-review
- Set: attsel
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: fqnj8k

## Workflow history

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from a defect the maintainer hit twice in one session and then asked to be filed rather than described in chat. MEASURED AT AUTHORING, all reproducible at HEAD `2aad4a98`: `aw att zzzzzz` -> no lines, exit 0; `aw att nosuchid` -> same; `aw att nosuchset-01` -> same; `aw att tests/nope.py` -> same; and the ambiguity proof, `aw att sv0sf3` (the real parked item `.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-...`) -> one line, exit 0, versus `aw att zzzzzz` -> zero lines, exit 0. In `--agent` mode both a real selector and a nonexistent one emit the identical `outcome:clean, exit:0, verified:true, complete:true, findings:0` record. THE CAUSE IS LOCATED, not guessed: `attention.filter_items_by_selectors` (`agent_workflows/attention.py:2635`) resolves each token against eight record types inside a bare `except Exception: pass`, collects matches into `matched_paths`, and returns a filtered LIST. A token that matched nothing is indistinguishable in that return value from a token whose matches were all filtered out downstream, and the caller (`:2806-2808`) simply replaces `items` with the result.

## Goal

Answer the operator's actual question. When they type a selector, they are asking "what is the state of
this thing?"; if the thing does not exist, that is the answer, and it is not the same answer as "nothing
needs attention."

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the two cases before changing any output

- [ ] E-01 REPRODUCE THE AMBIGUITY AS A TEST FIRST, so the fix has a falsifiable target and the claim above is proven rather than cited. Assert, at execution HEAD, that a nonexistent selector and a REAL-but-hidden artifact produce indistinguishable results today: same visible line count for the no-match case, same exit code, and in `--agent` mode the same `outcome`/`exit`/`findings` triple. Use a real hidden artifact rather than a synthetic one (a `parked` backlog item is hidden until `--all`; `sv0sf3` was the authoring-time example, but re-derive one at execution time rather than trusting that id to still be parked). This three-way fixture is the specification for E-03.
  - Depends on: none
  - Expected outcome: a pasted test run showing the two cases are currently indistinguishable in human output, exit code, and agent record.
  - Execution state: pending

- [ ] E-02 ENUMERATE EVERY SELECTOR FORM `filter_items_by_selectors` ACCEPTS, from the code rather than from this plan, and state per form how a NO-MATCH is currently detectable (it is not). Read `agent_workflows/attention.py:2635-2693`: the token is resolved against eight record types via `selectors.resolve_selectors`, then compared against `it.id`, `it.tree`, `it.attention_class`, `it.native_status`, `it.priority`, and finally a substring match on `it.path`. The substring rung is the one that matters most for this fix and is easy to miss: it means a token can match an artifact WITHOUT resolving as an identifier at all, so "did the selector resolve?" and "did the selector match?" are different questions and the fix must key on the second.
  - Depends on: none
  - Expected outcome: a pasted per-form table (form, where it is matched in the code, whether a no-match is currently reported), with the substring rung called out explicitly.
  - Execution state: pending

### Task group 2: report the no-match case, per token, without changing what is shown

- [ ] E-03 RETURN PER-TOKEN MATCH FACTS from the filter instead of only a filtered list, keeping the existing return shape working so no other caller changes meaning. The filter must be able to say, for each token, whether it matched at least one artifact ANYWHERE in the scan (before any class-based hiding) and whether it resolved to a real artifact path. Those are two different facts and both are needed: a token can resolve to a real artifact that is then hidden by default (matched, hidden) or resolve to nothing at all (no match). Do NOT widen what the view shows and do NOT auto-enable `--all`; this item only produces the facts.
  - Depends on: E-01, E-02
  - Expected outcome: a pure, tested function returning per-token match facts; the existing filtered-list behavior unchanged, proven by E-01's fixture still showing the same artifacts for a matching selector.
  - Execution state: pending

- [ ] E-04 REPORT A NO-MATCH SELECTOR IN THE HUMAN OUTPUT, naming the token and saying plainly that no artifact matched it. Where SOME tokens matched and others did not, report the unmatched ones individually rather than collapsing to one message, because a multi-token invocation is exactly where a single typo hides. Say what was searched (the tracked record trees) so the message is actionable rather than a bare negative. Do NOT print a remedy that guesses at intent (no "did you mean"): a wrong guess is worse than none, and the operator knows what they typed.
  - Depends on: E-03
  - Expected outcome: pasted output for a nonexistent selector naming the token; for a mixed invocation naming only the unmatched token(s); and for an all-matching invocation unchanged from today, shown side by side.
  - Execution state: pending

- [ ] E-05 MAKE THE `--agent` RECORD SAY IT TOO, which is the half that matters most for automation and is currently the most misleading. Today a nonexistent selector emits `outcome:clean, verified:true, complete:true, findings:0`, so a consumer records a typo as a clean audit. The record must distinguish the two cases in a machine-readable field rather than only in prose. HONOR THE SCHEMA: `agent_schema` admits `exit` values 0/1/2 only and requires an error record to carry exit 2, so pick a representation that validates, and if the honest representation cannot be expressed under the current schema, say so and record it as a finding rather than emitting an invalid record. Verify with the schema validator, not by eye.
  - Depends on: E-03
  - Expected outcome: the agent record for a no-match selector pasted, distinguishable from the matched-but-empty record, and shown passing `agent_schema` validation.
  - Execution state: pending

- [ ] E-06 DECIDE AND IMPLEMENT THE EXIT CODE for a no-match selector, and state the reasoning in the code rather than only in this plan. The argument for nonzero: the verb did not answer the question, and `aw check` already fails closed on a dangling `From-Backlog` for the same reason. The argument for 0: `attention` is a read-only reporting verb whose exit code today means "the view is valid", and scripts may already treat nonzero as "the repo is broken". If OQ-01 is unanswered, implement the STRICTER form (nonzero for a no-match) since that is the fail-closed direction, and make the code comment name the alternative so a later reader sees it was a decision.
  - Depends on: E-04, E-05
  - Expected outcome: the chosen exit code implemented and pinned by a test, with the reasoning and the rejected alternative recorded at the decision site in the code.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SUBSTRING RUNG MAKES "RESOLVED" AND "MATCHED" DIFFERENT QUESTIONS. `filter_items_by_selectors` ends with `if tok_lower in it.path.lower()` (`attention.py:2688`), so a token that resolves as no identifier can still legitimately match by path fragment. A fix that only asked `selectors.resolve_selectors` whether the token resolved would report a false no-match for every substring query.
- THE RESOLVER FAILURE IS ALREADY SWALLOWED. The per-record-type resolution sits inside `except Exception: pass` (`:2659-2661`), which is why a malformed selector is silent rather than refused. E-03 must not remove that tolerance (a raising resolver should not break the view) but must stop it from being indistinguishable from a clean answer.
- FAIL-CLOSED ON A DANGLING REFERENCE IS THE HOUSE PATTERN. `aw check` flags a `From-Backlog` or `From-Spec` value that resolves to no artifact (`check.from-backlog-dangling`, `check.from-spec-dangling`), and `AGENTS.md` records that a broken handoff claim is an error either way. A selector naming nothing is the same class of claim.
- `aw attention` IS READ-ONLY AND MUST STAY SO. `AGENTS.md` describes it as computing the view ON DEMAND with nothing committed. This plan adds output and possibly an exit code; it writes nothing.
- DEFAULT HIDING IS DELIBERATE, NOT A BUG. Terminal and `parked` artifacts are hidden until `--all` by design, and that is precisely what creates the ambiguity this plan fixes. The fix must not "solve" it by showing hidden artifacts.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `attention.filter_items_by_selectors` | **A NO-MATCH SELECTOR IS INDISTINGUISHABLE FROM A CLEAN ANSWER.** `aw att zzzzzz` prints nothing and exits 0; `aw att sv0sf3` (a real parked item) prints a line and exits 0. The operator cannot tell a typo from a quiet repo, and the only recovery is to leave the tool and grep. | measured at HEAD `2aad4a98`; `attention.py:2635` returning a bare filtered list |
| F2 | HIGH | the `--agent` record | **AUTOMATION RECORDS A TYPO AS A CLEAN AUDIT.** Both a real and a nonexistent selector emit `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`. `verified:true` and `complete:true` are both false in substance for a selector that matched nothing: nothing was verified and the answer is not complete, it is absent. | pasted agent records for `aw att zzzzzz --agent` and `aw att sv0sf3 --agent`, identical |
| F3 | MEDIUM | `attention.py:2659-2661` | The resolver runs inside `except Exception: pass`, so a MALFORMED selector is as silent as a merely-absent one. Worth separating in the fix: "this token is not a valid selector" and "this valid token matched nothing" are different messages, and conflating them would trade one ambiguity for another. | the bare except in the record-type loop |
| F4 | MEDIUM | `attention.py:2688` | THE SUBSTRING RUNG IS THE TRAP FOR THIS FIX. A token can match by path fragment without resolving as any identifier, so "did it resolve?" is the WRONG question. Keying the no-match report on the resolver alone would report a false no-match for every substring query, which is a worse defect than the one being fixed. | the final `if tok_lower in it.path.lower()` rung |
| F5 | LOW | `agent_schema` | THE HONEST AGENT RECORD MAY NOT FIT THE SCHEMA. `assert_valid_agent_record` admits `exit` in (0,1,2) and requires an error record to carry exit 2. If a no-match should be nonzero-but-not-an-error, the representation needs care; E-05 must validate rather than assume, and record a finding if no valid honest shape exists. | the schema's own exit constraint, observed while measuring an unrelated crash earlier in this session |
| F6 | LOW | this session's own history | THE COST IS REAL AND WAS PAID TWICE IN ONE SITTING. The maintainer ran `aw att 4fodkt` and `aw att 63425h`, got silence both times, and had to ask "where is this invisible plan?" Both were genuinely absent from `main` (an agent's unmerged worktree), so the tool was right that nothing matched and wrong to say nothing about it. | the session transcript; both plans later merged |

## Proposed changes (ordered, validatable)

1. Pin the current ambiguity as a three-way fixture (E-01) and enumerate every selector form from the code (E-02).
2. Return per-token match facts from the filter without changing what it filters (E-03).
3. Report unmatched tokens individually in human output, with no intent-guessing (E-04).
4. Make the agent record distinguish the two cases, validated against the schema (E-05).
5. Choose the exit code deliberately, implement the fail-closed default, and record the rejected alternative in code (E-06).

## Deferred / out of scope (with reason)

- EVERY OTHER VERB'S SELECTOR HANDLING. The same ambiguity plausibly exists in `aw find`, `aw ipd board` and others, but each has its own output contract and exit-code meaning, and widening this plan to all of them would make one change to N contracts at once. If E-02 finds the shared resolver is the right fix point for all of them, that is a FINDING and a follow-up plan, not a silent widening.
- A "DID YOU MEAN" SUGGESTION. Deliberately excluded: a wrong guess is worse than a clean negative, and the operator knows what they typed. Fuzzy matching is a separate feature with its own design question.
- CHANGING WHICH ARTIFACTS ARE SHOWN, or auto-enabling `--all` when a selector matches only hidden artifacts. Tempting and wrong: default hiding is deliberate, and quietly widening the view would hide the very distinction this plan exists to surface.
- THE SPURIOUS `TODO: Run /aw setup-repo` LINE that `aw attention` prints unconditionally, including on successful calls in a fully-configured repo. Real, adjacent, and its own item: it is a project-context defect rather than a selector one.

## Scope check

- Over-scope: none. Every item is contained in the selector-to-output path of one verb.
- Under-scope: none for the reported defect. The related verbs and the unconditional TODO line are deliberately deferred above with reasons.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). The gate is no NEW failures.
2. E-01's three-way fixture, pasted before and after, showing the no-match case becomes distinguishable while the matched-but-empty case is UNCHANGED.
3. A MULTI-TOKEN invocation where one token matches and one does not, showing only the unmatched one is reported.
4. A SUBSTRING selector (matching by path fragment, resolving as no identifier) shown NOT reported as a no-match: this is F4's regression guard and its absence would make the fix worse than the defect.
5. The `--agent` record for both cases, shown passing `agent_schema` validation rather than merely printed.
6. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change expected: `aw attention`'s selector behavior is verb behavior rather than a spec-defined
contract, and `- Scope-Paths:` therefore declares no `.spec.md`. If the executor finds spec text asserting
that `attention` exits 0 whenever the view is valid, THAT is a contract this plan changes: declare the spec
file in `Scope-Paths` before editing it, per the spec-amendment rule, and record the reason here rather
than changing behavior around it.

If E-06 changes the exit code, update `aw attention --help`'s documented exit meanings in the same change,
since a verb whose help still promises the old contract is worse than one with no documented contract.

## Open questions

### OQ-01: Should a no-match selector exit nonzero, or exit 0 with the message?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the plan is executable under either answer and E-06 implements the FAIL-CLOSED form by default (nonzero), which is the safe direction and is trivially relaxed later. FOR NONZERO: the verb did not answer the question asked, and this repository already fails closed on a dangling reference (`check.from-backlog-dangling`); a script that greps for an id6 and gets exit 0 with empty output will conclude "nothing to do", which is exactly the wrong conclusion. FOR ZERO: `attention` is a read-only reporting verb whose exit code today means "the view is valid", scripts may already treat nonzero as "the repo is broken", and a typo is an operator error rather than a repository defect. Recorded rather than decided because it is a public-contract call on a verb the maintainer uses interactively many times a day.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted three-way fixture result at execution HEAD showing (a) a nonexistent selector, (b) a REAL-but-hidden artifact, and (c) a matching visible artifact, with the human line counts, the exit codes, and the `--agent` `outcome`/`exit`/`findings` triples side by side, demonstrating that (a) and (b) are currently indistinguishable. State which artifact was used for (b) and that it was re-derived at execution time rather than taken from this plan.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted per-form table derived from an actual read of `filter_items_by_selectors` at execution HEAD (paste the code range or the search), naming every matching rung including the final substring rung, with an explicit statement of which rungs can match WITHOUT the token resolving as an identifier.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the per-token match facts pasted for a matching token, a non-matching token, and a token matching only a HIDDEN artifact, showing the three are distinguishable. PLUS proof the filtered list is unchanged: the same artifacts returned for a matching selector before and after, pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted human output for (a) a nonexistent selector naming the token, (b) a two-token invocation where exactly one is unmatched, showing only that one reported, and (c) an all-matching invocation shown byte-identical to today. PLUS the F4 regression guard: a substring selector that resolves as no identifier but matches by path, shown NOT reported as a no-match.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `--agent` records for the no-match and the matched-but-empty cases pasted side by side and visibly different, PLUS each shown passing `agent_schema.assert_valid_agent_record` (paste the validation call and its result, not an assertion that it validates). If no honest representation validates under the current schema, paste the failure and the recorded finding instead.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the chosen exit code demonstrated for all three fixture cases, the pinning test pasted green, and the code comment quoted showing the reasoning AND the rejected alternative are recorded at the decision site. If the exit code changed, the updated `--help` exit documentation quoted too.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (6 E-items in 2 task groups, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute with the FAIL-CLOSED form
(nonzero on a no-match) and do not guess a relaxation. SCOPE FENCE: this plan declares
`agent_workflows/attention.py` and `tests/test_attention.py`; an out-of-scope edit must be made only if
genuinely required and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared
path left unmodified needs a `--scope-ack`. NOTE, because this plan's own subject is a silent failure: a
fix that reports a FALSE no-match for a substring selector (F4) is a WORSE defect than the one being
fixed, so V-04's regression guard is mandatory rather than nice to have. THE HARD-MUST HONESTY RULE: paste
the ACTUAL command and test output for every `V-*`, never claim a run not performed, and never present an
agent record as schema-valid without pasting the validator's own result. Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours; this is a shared checkout with concurrent
sessions. After the gate, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`, and do not
claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed
evidence.
