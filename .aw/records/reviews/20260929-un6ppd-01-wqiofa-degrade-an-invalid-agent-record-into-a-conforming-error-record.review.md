# Review: Degrade an invalid aw.agent/v1 record into a conforming error record instead of a traceback

- Subject-Id: wqiofa
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `3324a45f`, working tree clean. `aw ipd lint --phase author --agent` reported
`clean` before any edit, so every finding below is semantic. Suite measured before any edit:
`3387 passed, 2 skipped, 3 warnings in 60.65s`.

THE PLAN'S DIAGNOSIS IS EXCELLENT AND ITS TWO CORRECTIONS OF THE BACKLOG ITEM ARE BOTH RIGHT.
F-01 reproduces exactly: `BaseRenderer.emit` wraps only `ctx.stdout.write`/`flush`, so the
`render` call that raises sits outside every handler. F-02 reproduces on all three verbs from a
plain command line: `attention <home path> --agent`, the same with `--json`, and
`runs <home path> --agent` each exit 1 with zero stdout bytes and a `ValueError`, while the human
path of the same command exits 2 with a clean message, confirming the crash is machine-surface
specific. F-06, the correction that changes the design, reproduces decisively: a substitute
carrying the validator's message verbatim RE-TRIPS the unsanitized-path rule
(`Unsanitized absolute home path in field 'error': "Invalid aw.agent/v1 record: ..."`) while the
ANSI, bad-exit and bad-outcome classes do not, and a rule-text-only substitute validates clean for
every class. F-04, F-07, F-08, F-09, F-10 (including commit `5adf3774` and the now-fixed projection
case), F-13, F-14 and F-15 all verify as written, and all three carrier items exist and are live
with `enygec` carrying `- Blocks-Release: next` at `- Work-Kind: bug`.

THE PLAN IS ALSO UNUSUALLY HONEST ABOUT ITS OWN LIMITS. Its Scope check, Deferred section, gate
prose and a required test all state that the three most visible crashes SURVIVE it. That is the
right call and it is argued from evidence (routing them through the guard would mask an
unsanitized-input defect), not asserted.

BUT ONE PROBLEM IS STRUCTURAL AND I CANNOT REPAIR IT WITH BOUNDED EDITS, SO IT IS ESCALATED
BLOCKING. E-04 requires `BaseRenderer.emit` to "return exit code 2 when the agent renderer
substituted a record", and there is NO MECHANISM by which it can know. `render()` returns a bare
`str` on the shared `BaseRenderer` contract, `emit` is defined ONCE on `BaseRenderer` and inherited
unmodified by all three renderers, and it returns `result.exit_code` to 98 call sites. So the plan
asks for a value that cannot be computed without one of three unstated designs: parsing the emitted
line back, a side-channel on `self` or the context, or changing the `render()` signature that
`HumanRenderer` and `JsonRenderer` also implement, which the plan's own Scope check forbids
("`HumanRenderer` and `JsonRenderer` are not modified"). Worse, the parity rule E-04 invokes is not
even well defined for the path it also changes: `render_stream` returns `"".join(lines)`, a
MULTI-LINE payload, so "the embedded `exit` equals the process exit code" has no single referent
when one item line of forty is substituted. This is a design hole, not a wording slip, and choosing
among the three mechanisms is a public-contract decision (PR-201, escalated as blocking OQ-05).

Three further real problems, all fixed in place.

F-12's SUITE BASELINE IS STALE BY 141 TESTS. It records `3246 passed, 2 skipped` and the plan makes
that number a comparison target in Required tests and V-05. Measured at this HEAD: `3387 passed, 2
skipped`. An executor comparing totals against 3246 would report a 141-test discrepancy as a
regression it did not cause (PR-202).

E-01's RULE-TEXT REDUCER IS UNDERSPECIFIED IN THE ONE DIRECTION THAT MATTERS, and the obvious
implementation is wrong for two of the five classes. The natural reading of "reduce to its RULE
PREFIX" is a split on the first colon. Measured, that is safe for the path and ANSI classes but it
MANGLES two others: the `Unknown outcome` message contains no colon before its value, so a
colon-split returns the ENTIRE message including the offending value; and `Field 'exit' must be an
integer in (0, 1, 2), got '7'` contains a colon nowhere either, so the same applies. Neither leaks a
home path, so the no-leak probe V-02 demands would pass while the reducer silently fails its stated
contract of "discarding the quoted offending value" (PR-203).

E-01's NO-LEAK ASSERTION AS WRITTEN CANNOT FAIL for the ANSI class. It says to assert `_HOME_PATH_RE`
does not match and `_ANSI_ESCAPE_RE` does not either, given "the error list produced by a record
carrying an unsanitized home path". A home-path record's message contains no ANSI escape to begin
with, so the ANSI half of that assertion is vacuous on the input named. It must be asserted against
the ANSI class's own message, where I verified it does hold (PR-204).

Two smaller items: the F-07/OQ-03 gloss `"A fatal or cannot-run execution diagnostic"` is quoted as
`docs/cli-agent-protocol.md`'s kind table but actually lives in `docs/cli-output-contract.md` line
181, and that document IS in `Scope-Paths` so the misattribution would send an executor to amend the
wrong file (PR-205); and F-05's fourth violation class only fires under `--verbose`, which the plan
does not say, so a compact-mode probe finds no crash and looks like a failed reproduction (PR-206).

NOTE ON THE ARRIVING LIFECYCLE STATE, which is a near miss worth recording. The plan's
`## Workflow history` is ordered oldest-first, like the two previous plans in this sweep. It does NOT
currently fail `aw check plans`, because `check_lifecycle_transitions` groups same-date events and
treats an unordered same-date group as unvalidated, and both existing lines are 2026-09-29. Adding
my own 2026-09-30 line flips that group to `ordered=True` and WOULD have made it fail. I swapped the
pair, verified `draft -> to-review -> reviewed` now validates, and record this because the defect was
latent rather than absent (PR-207).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | BLOCKER | IN-SCOPE | C. Architecture / A. Correctness | `renderers.BaseRenderer.emit` (defined ONCE, `return result.exit_code`, inherited by all three renderers); `BaseRenderer.render` return annotation is `str`; `AgentRenderer.render_stream` returns `"".join(lines)`; 98 `.emit(` call sites across `agent_workflows/` | E-04 REQUIRES A VALUE `emit` CANNOT COMPUTE. It says to "make `BaseRenderer.emit` return exit code 2 when the agent renderer substituted a record", but `render()` returns a bare `str`, so no substitution signal crosses that boundary. Every available mechanism is unstated and each has a cost the plan never weighs: parse the emitted line back (fragile, and re-parsing your own output to learn what you just did is a smell), a side-channel on `self` or the context (makes the renderer stateful, and `emit` is shared with the two renderers the plan promises not to modify), or widen `render()`'s signature (a public contract change across all three renderers, contradicting this plan's own Scope check). SEPARATELY, the parity rule E-04 invokes is ill-defined for `render_stream`, which returns a MULTI-LINE payload: when one item line of forty is substituted, "the embedded `exit` equals the process exit code" has no single referent, and the other thirty-nine lines are already valid and already in the string. Choosing a mechanism is a published-contract decision reserved to the maintainer. | C:Medium-High; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED as blocking OQ-05 with `- Finding: PR-201`, enumerating the three mechanisms with the cost of each and naming the `render_stream` multi-record ambiguity as a sub-question. E-04 annotated with a `Blocked by: OQ-05` note and its Expected outcome narrowed to the single-record case. NOT fixed on reviewer authority: the fix bar is Medium-High on complexity and functionality, and every option either changes a shared public signature or makes a renderer stateful. |
| PR-202 | HIGH | IN-SCOPE | Step 1 evidence accuracy / E. Testing | Bare `python3 -m pytest` at HEAD `3324a45f`: `3387 passed, 2 skipped, 3 warnings in 60.65s`; F-12 records `3246 passed, 2 skipped` | THE BASELINE IS STALE BY 141 TESTS AND IS USED AS A COMPARISON TARGET TWICE (Required tests and V-05 both say "against the F-12 baseline of `3246 passed, 2 skipped`"). An executor following V-05 literally would compare its post-change total against 3246 and find a 141-test gap it did not cause, then either report a phantom regression or spend a cycle bisecting it. The plan's own V-05 wisely says to compare failing NODE IDS rather than totals, which is the right method and is contradicted by the number beside it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 re-measured to `3387 passed, 2 skipped, 3 warnings` at HEAD `3324a45f` with a note that the figure is a live population that drifts and that node-id comparison governs; Required tests and V-05 updated to the new figure and to lead with the node-id rule. |
| PR-203 | HIGH | IN-SCOPE | A. Correctness / E. Testing | Measured on all four classes: `"ANSI escape code detected in field 'next': '\x1b[...]'"` splits safely at the first colon, and so does the path rule, but `"Unknown outcome 'nonsense'; expected one of (...)"` and `"Field 'exit' must be an integer in (0, 1, 2), got '7'"` contain NO colon before their offending value, so a first-colon split returns the WHOLE message | E-01'S REDUCER IS UNDERSPECIFIED AND THE OBVIOUS IMPLEMENTATION SILENTLY FAILS ITS OWN CONTRACT FOR TWO OF FIVE CLASSES. "Reduce each string to its RULE PREFIX, discarding the quoted offending value" reads as a first-colon split, which works for exactly the two classes E-01 names in its Expected outcome (home path, and `exit` field-name survival) and mangles the other two by returning the offending value intact. The failure is INVISIBLE to the no-leak probe V-02 demands, because neither residue is a home path or an ANSI escape, so the plan's own strongest check cannot catch it. The `exit` case is doubly awkward: E-01 requires the FIELD NAME to survive there, which a colon-split does achieve, but only by keeping the whole message including `got '7'`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now states the measured per-class behavior, requires the reducer to be defined against the validator's ACTUAL message shapes rather than a single delimiter heuristic, and requires a positive assertion per class that the offending value is ABSENT from the reduced text (not merely that no home path or ANSI escape is). Added F-16 with the four measurements. V-01 requires the per-class table pasted. |
| PR-204 | MEDIUM | IN-SCOPE | E. Testing | E-01's Expected outcome asserts, for "the error list produced by a record carrying an unsanitized home path", that `_ANSI_ESCAPE_RE` "does not either" match; a home-path message contains no ANSI escape, so the assertion is vacuous on that input | THE ANSI HALF OF E-01'S NO-LEAK ASSERTION CANNOT FAIL ON THE INPUT IT NAMES. Asserting the absence of something the input never contained proves nothing, and a reader of the Expected outcome would reasonably believe ANSI redaction was covered. Verified separately that the property DOES hold when asserted against the ANSI class's own message, so this is a mis-targeted assertion and not a broken property. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01's Expected outcome now targets each regex at the class whose message can actually contain that residue, and says why (an assertion that cannot fail is not coverage). |
| PR-205 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | The string `A fatal or cannot-run execution diagnostic` occurs at `docs/cli-output-contract.md:181`; `grep` finds it NOWHERE in `docs/cli-agent-protocol.md`, whose kind table row for `kind` reads only "One of `result`, `summary`, `item`, `error`." with no gloss | F-07 AND OQ-03 ATTRIBUTE A REAL QUOTE TO THE WRONG DOCUMENT. Both say "`docs/cli-agent-protocol.md`'s kind table glosses `error` as 'A fatal or cannot-run execution diagnostic'". The quote is verbatim correct and the reasoning it supports is sound, but it lives in the OTHER contract file. This matters more than a normal citation slip because BOTH files are in `- Scope-Paths:` and E-05 amends both, so an executor tracing the justification would look in the wrong file for the sentence their amendment must sit beside. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 and OQ-03 both re-attributed to `docs/cli-output-contract.md:181`, with a note that `cli-agent-protocol.md`'s kind table carries no gloss so E-05's amendment there is additive rather than adjacent to existing prose. |
| PR-206 | LOW | IN-SCOPE | Step 1 evidence accuracy | Measured: a diagnostic `fix` carrying a home path raises ONLY with `verbose=True` (compact mode drops `fix` and `detail`, keeping just `location` and `rule` per `CommandResult.to_agent_record`); same for an evidence `detail` | F-05'S FOURTH VIOLATION CLASS HAS AN UNSTATED PRECONDITION. The row lists "a home path in an `evidence` detail or a diagnostic `fix`" beside the third class which it DOES mark `(verbose)`. In compact mode `to_agent_record` projects diagnostics to `location` and `rule` only, so the fourth class does not fire at all. An executor probing it compactly finds no crash and reads that as a failed reproduction of the plan's own evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 now marks the fourth class `(verbose only)` with the projection reason, and E-05's class enumeration inherits the qualifier so each probe is constructed in the mode that reaches it. |
| PR-207 | MEDIUM | IN-SCOPE | G. Plan executability / lifecycle | `_plan_status_events` on the as-committed text derives `[to-review, draft]`; `check_lifecycle_transitions` skips a same-date group whose `ordered` flag is False, which is why `aw check plans` did NOT flag it; adding a later-dated line flips that group to `ordered=True` | THE HISTORY IS ORDERED OLDEST-FIRST AND THE DEFECT IS LATENT RATHER THAN ABSENT. Unlike the two previous plans in this sweep, this one escapes `check.lifecycle-transition-invalid` today, but only by the accident that both its entries share one date and the checker treats an unordered same-date group as unvalidated. Appending any later-dated entry (which every subsequent workflow does) flips the group to ordered and makes the backwards `to-review -> draft` transition validate and fail. So the plan was one history line away from failing the repository's own check. Third instance of this ordering defect in three consecutive plans, which points at the authoring path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Swapped the two lines into newest-first order BEFORE appending the review record. Verified with the shipped predicates that the groups now derive `draft -> to-review` and `to-review -> reviewed`, both `ok=True`, and `aw check plans --agent` reports 0 findings naming this plan. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-201: should the reviewer pick one of the three substitution-signal mechanisms, or escalate? | ESCALATE as blocking OQ-05, enumerating all three with costs and naming the `render_stream` sub-question | Pick the side-channel (least invasive but makes a shared renderer stateful); pick line re-parsing (no signature change but fragile and re-reads its own output); widen `render()` (cleanest but a public contract change across three renderers the plan promises not to touch) | No repository artifact answers it. Every option changes something the plan's own Scope check protects, or changes a signature 98 `emit` call sites and two other renderers share, so the fix bar is Medium-High on complexity AND functionality. Which cost to accept is an architecture and public-contract call reserved to the maintainer. The `render_stream` multi-record ambiguity has no precedent in either contract doc to read off | no |
| D-2 | Is the plan's core direction (guard at the serializer, rule text only, substitute strictly validated) sound enough to keep despite PR-201? | Keep it; the blocker is confined to E-04's exit-code half | Mark REPLAN, which would discard a correct and well-measured diagnosis over one unresolved mechanism | E-01 through E-03 are independently sound and independently verifiable, and I reproduced their premises directly: the rule-text-only substitute validates clean for every class, the floor record validates clean, and the strict/guarded split has a shipped precedent. Only the `emit` exit-code coupling is unresolved, and OQ-05 localizes it | yes |
| D-3 | PR-202: re-measure the baseline myself, or instruct the executor to? | Re-measure now and write the number in, keeping the node-id rule as the governing method | Replace the number with "re-measure at execution", which is the live-artifact convention | Both: the convention says a live count belongs in prose as context and the PROPERTY is the bar, so I recorded the fresh number AS context and promoted node-id comparison to the actual criterion. Leaving a stale 141-off number in place would have an executor chasing a phantom regression | yes |
| D-4 | PR-203: should the reviewer specify the reducer's exact algorithm? | No: specify the REQUIRED PROPERTY per class and the measurements, and let the implementer choose the mechanism | Prescribe a concrete algorithm (for example, split on the last `: '` occurrence), which would be a HOW answer I have not demonstrated on all five classes | The plan-review rule on HOW questions: a mechanism may be marked resolved only with a demonstration on a concrete case. I measured that the naive split FAILS for two classes but did not build and prove a replacement, so specifying the property (the offending value must be absent, asserted per class) is the honest boundary | yes |

### Round 1 close

Six of seven findings FIXED in place. PR-201 is left OPEN at BLOCKER severity and is therefore
ESCALATED into the plan as OQ-05 carrying `- Blocking: yes` and `- Finding: PR-201`, per the gate
threshold rule, so `aw ipd lint` refuses the plan at every checkpoint until the maintainer answers.
`- Readiness: no-go` is written accordingly: the plan carries an unresolved blocking question and an
unfixed BLOCKER, which is the genuine not-ready condition the vocabulary reserves that value for.

The four pre-existing open questions (OQ-01 through OQ-04) were each independently re-verified and
all four remain correctly `resolved`; OQ-03's supporting citation was re-attributed per PR-205
without changing its conclusion.

## Round 2

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-201 | blocker | IN-SCOPE | C. Architecture / A. Correctness | `renderers.BaseRenderer.emit` (defined ONCE, `return result.exit_code`, inherited by all three renderers); `BaseRenderer.render` return annotation is `str`; `AgentRenderer.render_stream` returns `"".join(lines)`; 98 `.emit(` call sites across `agent_workflows/` | E-04 REQUIRES A VALUE `emit` CANNOT COMPUTE. It says to "make `BaseRenderer.emit` return exit code 2 when the agent renderer substituted a record", but `render()` returns a bare `str`, so no substitution signal crosses that boundary. Every available mechanism is unstated and each has a cost the plan never weighs: parse the emitted line back (fragile, and re-parsing your own output to learn what you just did is a smell), a side-channel on `self` or the context (makes the renderer stateful, and `emit` is shared with the two renderers the plan promises not to modify), or widen `render()`'s signature (a public contract change across all three renderers, contradicting this plan's own Scope check). SEPARATELY, the parity rule E-04 invokes is ill-defined for `render_stream`, which returns a MULTI-LINE payload: when one item line of forty is substituted, "the embedded `exit` equals the process exit code" has no single referent, and the other thirty-nine lines are already valid and already in the string. Choosing a mechanism is a published-contract decision reserved to the maintainer. | C:Medium-High; U:Low; S:Low; F:Medium-High; Overall:Medium-High | fixed | STALE ESCALATION CLOSED 2026-10-02 by agent (aw ipd recheck-readiness). The question this finding was escalated as (OQ-05) is `- Status: resolved`, so the finding it gated on has been answered and the record is caught up. NO FINDING WAS RE-DERIVED and no plan content was re-critiqued: the match was made on the question's declared `- Finding: PR-201` back-reference, not on a judgement about what the question was about. Previous decision: open. |
