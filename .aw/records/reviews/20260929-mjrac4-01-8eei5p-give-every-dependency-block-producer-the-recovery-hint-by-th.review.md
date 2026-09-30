# Review findings: plan 8eei5p

- Subject-Id: 8eei5p
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401, PR-402 (MEDIUM, fixed), PR-403 (LOW, fixed)

## Round 1

Reviewed at lane HEAD `63c7da25` in an isolated review lane. The plan file was committed and unchanged,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize --agent` reports
`conforming` after revision.

THE PLAN IS WELL EVIDENCED AND ALMOST EVERYTHING IN IT REPRODUCES. I drove every material claim rather
than reading it. F-01's central staleness argument holds: calling the real `cascade_dependency_blocked`
over a state with a `failed-safely` prerequisite yields `deps: ['executed:aaa111']` and
`reasons: {'executed:aaa111': 'target aaa111 is failed-safely'}` with no recovery key, so the backlog
item's headline claim (reason embedded in the token, no reasons map) really is false at HEAD and the plan
is right to refuse to repeat it. F-02 reproduces end to end through the shipped `write_report`: two items
differing only in the presence of `dependency_block_recovery` render sections that differ by exactly one
`- Recovery:` line, and `grep` confirms two drain writes and a single reader. F-03's constants differ
only in `aw oc` versus `aw agy` and compare unequal. F-06's TERMINATE block writes the two dependency
keys and no recovery key, as read. F-07's `children-unfinished` remedy is verbatim, including the
`aw ipd set approved <id6> --by-human` clause. F-08's `fail-depend` is in the requeue status set and both
exclusions evaluate False for all three producers' real item shapes. F-10's single pinning assertion and
the event-key equality assertion are both present at the lines the plan implies. F-13 is exactly right:
`HostLabels._fields` is ten fields, `SCRIPTED_HOST_LABELS` is built by literal keyword at module scope
(so a no-default eleventh is an import-time `TypeError`), and `test_set_plan_approved_durable_history_pin`
derives its kwargs from `_fields` and needs no edit while still pinning the no-default property. F-15
finds no spec mentioning either the key or the section. All five cited carriers are in their stated
states, including `phawyy`, which really was retracted and really is `parked`.

F-04 IS THE FINDING I EXPECTED TO BE SOFT AND IT IS THE OPPOSITE. The plan rejects half of its own
backlog item's suggested fix, which is the kind of refusal that usually rests on an argument rather than
a measurement. Here it rests on a measurement: composing the shipped `if d in why` expression against a
frozen-shape token yields `executed:aaa111 (target reviewed)`, while the blanket
`reasons.get(d, "unsatisfied")` form yields `executed:aaa111 (target reviewed) (unsatisfied)`, and the
two shipped assertions the row names (`"(blocked)" not in out` in three places, plus the inline-reason
row in `test_run_selection_policy.py`) do exist. So the deletion the item asks for would both regress
frozen-record rendering and turn shipped tests red. F-05's companion argument, that declining costs the
item's goal nothing because a complete reasons map always satisfies a presence test, is sound.

WHAT REVIEW FOUND. Two corrections, both in instructions to the executor rather than in the plan's
reasoning.

FIRST, E-03 and F-11 contradict each other inside the same plan about how many call sites a required
parameter would break. E-03's prose says "Five test call sites" and then parenthetically lists SEVEN
filenames; F-11 says NINE. I counted: nine invocations across six files
(`test_dependency_block_reporting.py` 2, `test_terminal_status_vocabulary.py` 2,
`test_runner_shared.py` 2, and one each in `test_host_capability_wiring.py`,
`test_orchestrator_retirement.py`, `test_oc_runipd.py`), with `test_finalize_sendback.py` naming the
symbol in an identity pin without calling it. F-11 was right. This matters because E-03's paragraph is
the one an executor reads while deciding whether the `None` default is worth the trouble, and an
under-count of nearly half makes a required parameter look cheaper than it is.

SECOND, AND THE ONE THAT WOULD HAVE COST A TURN: E-05 tells the executor to "run the host's
`retry_incomplete` requeue path over it" and V-05(c) requires confirming the measurement "drove the REAL
requeue branch (naming the function called) rather than re-implementing its status set". There is no such
function. The `if retry_incomplete:` block lives in the body of each host's `run_queue`, and the only
requeue callable anywhere in either host or `runner_shared` is `requeue_interrupted(run_dir, state)`,
which is the different interrupted-prerequisite route. So an executor obeying V-05(c) literally has three
options: fabricate a function name, re-implement the status set (which the same clause forbids), or drive
a whole `resume --retry-incomplete` end to end, which the plan never mentions. I made the third option
explicit, added a labelled weaker alternative, and required the route be declared. I also measured the
expected answer so the executor confirms rather than derives it: both exclusions return False for all
three producers and `fail-depend` is in the shipped set, so all three requeue.

THE ITEM-BY-ITEM DESIGN IS RIGHT AND I DID NOT DISTURB IT. The descriptor-field choice is argued from
`orchestrator_uncovered_work_remedy`'s own docstring naming this exact constant, and I confirmed that
docstring says so; the shared-constant alternative really is mechanically forbidden by
`test_no_divergent_codefined_constants_in_runner_shared`, whose AST collection and value comparison I
read. E-04's RECONSIDER prohibition is the sharpest thing in the plan: it identifies the one edit that
would ship a FALSE statement rather than a missing one, sources the prohibition from
`TRANSIENT_DEPENDENCY_WAIT_HINT`'s own comment, and V-04 makes it a falsifying case. E-07's framing (not
incidental test maintenance, and an executor who meets it as a collection error will reach for a default
and defeat E-01) is exactly the right warning, and F-13 measures why.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | MEDIUM | IN-SCOPE | Evidence accuracy (self-contradiction) | Scripted count over `git ls-files 'tests/*.py'` matching `cascade_dependency_blocked\s*\(`: 9 invocations across 6 files (`test_dependency_block_reporting.py` 2, `test_terminal_status_vocabulary.py` 2, `test_runner_shared.py` 2, `test_host_capability_wiring.py` 1, `test_orchestrator_retirement.py` 1, `test_oc_runipd.py` 1); `test_finalize_sendback.py` names it in an identity pin without calling it; plan E-03 versus F-11 | **E-03 says "Five test call sites" where F-11 in the same plan says NINE, and E-03's own parenthetical then lists SEVEN filenames.** F-11 is correct. The paragraph is the one an executor reads while judging whether the keyword-only `None` default is worth it, so an under-count of nearly half makes a required parameter look cheaper than it is, and a plan that disagrees with itself about a countable fact invites a reader to discount both numbers | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 corrected to NINE with the per-file breakdown inline, the `test_finalize_sendback.py` non-call distinguished, and the correction flagged so a reader sees which number was wrong. F-11 gained its counting rule and its exclusion so the figure is checkable rather than asserted, plus a note that E-03's prose was the error and this row was right |
| PR-402 | MEDIUM | IN-SCOPE | G. Plan executability (an instruction that cannot be followed) | `dir()` over `oc_runipd`, `agy_runipd` and `runner_shared` for any `requeue`/`retry_incomplete` callable returns only `requeue_interrupted(run_dir, state)`; `inspect.getsource(oc_runipd.run_queue)` locates the `if retry_incomplete:` block inside it; plan E-05 and V-05(c) | **E-05 says to "run the host's `retry_incomplete` requeue path over it" and V-05(c) requires "naming the function called", and no such callable exists.** The branch is inline in each host's `run_queue`, and the only requeue function is the different interrupted-prerequisite route. An executor obeying V-05(c) literally must either fabricate a function name or re-implement the status set, which the same clause forbids; the one honest route (drive a real `resume --retry-incomplete`) is never mentioned. Since E-05 is the item that gates the plan's entire uniformity premise, an unsatisfiable instruction there risks either a fabricated claim or the item being quietly skipped | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-18 records the absent callable, the inline branch, and the contradiction between the two clauses. E-05 now names TWO acceptable routes (end-to-end `resume --retry-incomplete`, preferred; or predicate-level with the limitation explicitly declared) and states that the anti-reimplementation clause cannot otherwise be met. V-05(c) rewritten to require the route be NAMED and to forbid claiming a function call that does not exist, with the weaker route's evidence shape spelled out. Review also measured the expected answer (both exclusions False for all three producers, `fail-depend` in the shipped set), so the executor confirms rather than derives it; Required tests item 3 reconciled |
| PR-403 | LOW | IN-SCOPE | Live-artifact figure quoted as context | Bare `python3 -m pytest` at review HEAD: `3284 passed, 2 skipped, 3 warnings`, against the authored `3246 passed, 2 skipped` | **The recorded baseline has drifted by 38 tests since authoring.** F-17 already says the digits are context and not the bar, which is the correct disposition, so this is a refresh rather than a defect; recording the measured drift is what makes the row's own warning concrete instead of theoretical | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-17 gained the review measurement and names the 38-test rise as the reason it refuses to be an acceptance bar. Also added F-19, F-20, F-21 and F-08b, which record that the three-write-site census E-02 must re-home is where the plan says and its item 1 says exactly what E-02 claims, that all three descriptor guardrails hold as assumed, that the report section gates on the canonical status plus either dependency key so the additive write needs no consumer change, and that `write_report` requires `setid` on every probe item (review hit the `KeyError` building one) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-402: should E-05 mandate the end-to-end route, or permit a predicate-level measurement? | Permit both, with end-to-end preferred and the weaker route required to declare its limitation | Mandating end-to-end only; dropping E-05 and resting on F-08's source read; leaving E-05 as written | Mandating end-to-end is defensible but expensive: it requires preparing a real run directory per producer, and the orchestrator TERMINATE case needs a Set with unfinished children, so the cost could push an executor to skip the item entirely, which is worse than a labelled weaker measurement. Dropping E-05 is wrong because the uniformity premise is the plan's foundation and F-08 is a source READ, exactly what E-05 exists to replace. Leaving it as written is not viable since it cannot be satisfied honestly. Requiring the route be NAMED preserves the audit value either way: a reader can see what was actually established | yes |
| D-2 | PR-401: which of the plan's two contradicting counts is authoritative? | F-11's nine, verified by counting invocations myself | Taking E-03's five; taking the seven its own list implies; leaving both and noting the discrepancy | I counted rather than arbitrating: nine invocation sites across six files, which matches F-11 exactly. E-03's five matches nothing, and its seven-filename list double-counts two files that hold two calls each while omitting none, so the list was a file census presented as a call census. Leaving both numbers standing was rejected because the plan then contains a countable self-contradiction that a validator would trip over and that makes its other figures less credible | yes |
| D-3 | F-04 rejects the backlog item's own suggested second half. Should review uphold that, given the item is the plan's mandate? | Uphold it; the measurement is decisive | Reinstating the deletion as an E-item; escalating to the maintainer as an open question; splitting it into a follow-on plan | The measurement settles it without needing anyone's judgement: the blanket fallback demonstrably produces `(target reviewed) (unsatisfied)` on frozen records, and two shipped assertions (`"(blocked)" not in ...` in three places, plus the inline-reason row) would turn red. An item's suggested fix is a hypothesis, not a specification, and `5o1jye` E-03 landed the surviving conditional deliberately as a frozen-record reader. Escalating would ask the maintainer to re-decide something the tree already answers. The plan's honest reframing (no PRODUCER divergence remains; the reader is back-compat, not a special case) reaches the item's stated goal by a different route, which is the right disposition | yes |
| D-4 | E-04 forbids the RECONSIDER path from receiving the hint. Should review test that prohibition or accept it? | Accept it, and note that V-04 already makes it a falsifying case | Driving the RECONSIDER path myself to confirm it leaves the item `queued`; weakening it to a recommendation | The prohibition is sourced from `TRANSIENT_DEPENDENCY_WAIT_HINT`'s own comment, which states that such an item "needs no flag at all" and that saying otherwise "would send the operator to a flag they do not need", so it rests on in-tree text rather than on the author's judgement. V-04(c) already requires driving RECONSIDER with the hint supplied and showing the key ABSENT, and states that V-04 fails outright if the key appears, which is the strongest form this can take in a plan. Weakening it would be actively harmful: this is the one edit in the plan that would ship a false instruction rather than a missing one | yes |
