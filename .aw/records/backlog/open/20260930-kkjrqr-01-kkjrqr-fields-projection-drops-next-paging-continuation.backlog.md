- Id: kkjrqr
- Status: open
- Blocks-Release: next
- Set: kkjrqr
- Priority: medium
- Work-Kind: bug
- Summary: a --fields projection drops a summary's next paging continuation, so a truncated agent answer can carry no command to retrieve the rest

## Workflow history
- 2026-09-30 created (aw backlog): a --fields projection drops a summary's next paging continuation, so a truncated agent answer can carry no command to retrieve the rest

MEASURED 2026-09-30 while authoring plan `mcdvx0` from backlog item `cm80ge`.

`agent_schema._PRESERVED_FIELDS` is the set a `--fields` projection may not remove. Plan `gygujf` widened it to `_MANDATORY_FIELDS | {applied, total, emitted, omitted}` so that a projection can never yield a record the validator rejects. `next` IS NOT IN THAT SET, and it is not required by `validate_agent_record`, so a projected record is still VALID without it. That is why `gygujf` correctly did not add it: the defect it fixed was validity, and this one is not a validity defect.

THE OBSERVABLE PROBLEM IS PAGING, NOT VALIDITY. `run_analytics_query` sets `next_command` exactly when rows were omitted (`if omitted:`), and a summary record reports `complete: false` with `omitted > 0`. Under `--fields` the `next` key is dropped, so an agent receives a record that says an answer is INCOMPLETE while withholding the one field that says how to get the remainder. `next` is not reconstructible by the caller: it encodes the view, the active filters, and `--limit min(total, MAX_ROW_LIMIT)`, so the caller cannot rebuild it from the record it holds.

MEASURED, on `AgentRenderer().render_summary('runs query', total=5, emitted=2, omitted=3, outcome='clean', exit_code=0, next_cmd='aw runs query --offset 2', complete=False, ...)`:
- no context: emits `...,"complete":false,"next":"aw runs query --offset 2"}`
- `fields=['cmd']`: emits `...,"complete":false}` with NO `next`
- `fields=['next']`: retains it
- `'next' in agent_schema._PRESERVED_FIELDS` is `False`

WHY IT IS FILED AS A BUG rather than a chore: a user-facing contract document promises the stronger thing. `docs/cli-agent-protocol.md` tells a reader 'A projection never yields a record that fails validation, so `--fields` is safe to pass on any command', and the agent protocol's whole paging affordance is the `next` command. An agent that passes `--fields` to reduce tokens silently loses its continuation on exactly the bounded answers where it needs one, and it cannot tell that it happened. That is user-perceptible behavior (a stranded pagination), not an internal inefficiency.

NOT A REGRESSION FROM `gygujf`: this behavior predates it. `gygujf` is only how it became visible, because widening `_PRESERVED_FIELDS` left `next` as the single remaining droppable field of consequence on a summary.

CANDIDATE FIXES, not yet decided, and the choice needs a contract decision rather than a code preference:
(a) add `next` to `_PRESERVED_FIELDS`, which is one line and makes every projected summary carry its continuation. Cost: `next` is the longest field on the record, so it partly defeats the token saving `--fields` exists for, and it is retained even when `complete: true` (where it is `None` and omitted anyway, so the real cost is only on truncated answers).
(b) preserve `next` CONDITIONALLY, only when `complete` is false. Honest but introduces the per-kind conditional logic `gygujf` deliberately rejected in favor of a flat kind-independent set, so it would reopen the coupling that plan closed.
(c) document the drop and leave behavior alone, which requires amending the protocol doc's 'safe to pass on any command' framing.

Whichever is chosen, the test must assert on emitted records from a real bounded query rather than on the constant's contents, per P16.

FILED BY `mcdvx0` as the carrier for its explicitly deferred question; that plan only DESCRIBES this behavior in a code comment and changes none of it.
