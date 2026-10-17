# Workflow: plain

Rewrite your previous message so a capable engineer who has not seen this work can understand it.
The user asked for this because the message did not make sense to them. Treat that as a fact about
the message, not something to argue with.

## What to rewrite

- With no arguments, rewrite your most recent message in full.
- With arguments, they name which part to rewrite or what was unclear. Rewrite that part, keeping the
  rest of the message consistent with it.

## How

1. Write for a reader who knows software but not this repository, this session, or what you found.
2. Say what each thing does before naming it. Explain every term, project name, and identifier the
   first time it appears. An identifier or filename never replaces the explanation.
3. For a failure or blocker, tell what happened in order: what was observed, what caused it, what
   that led to, and what fixes it. If the cause is not verified, say "cause not verified" instead of
   stating a mechanism. A fluent wrong explanation is worse than an honest gap.
4. Keep every fact, number, and decision from the original. Do not add new claims you have not
   checked. Do not drop a caveat to make the text read more smoothly.
5. Length is not the goal in either direction. The word cap for routine reports does not apply here.

Then send the rewrite. Do not defend the earlier version, apologize at length, summarize what you
changed, or append anything else.

## Example

Before (accurate, compact, and understandable only to someone who already knew the answer):

> One pre-existing test flake burned 2 hours and $33, and the 'external target' diagnostics are a
> red herring. `tests/test_term.py` races under xdist: those tests mutate process-global
> `os.environ` (`NO_COLOR`/`FORCE_COLOR`/`TERM`), and `addopts` runs `-n auto --dist=worksteal`, so
> workers cross-contaminate.

After:

> One test fails at random, and that cost two hours and $33 of the overnight run. The warnings
> about an "external target" were unrelated.
>
> The tests in `tests/test_term.py` change environment variables such as `NO_COLOR` and `TERM`, which
> control terminal colors. The suite runs tests in parallel, and the failure moves to a different
> test on each run, which points at those tests affecting each other. The exact way they interfere
> is not verified yet: the parallel workers are separate processes, so they should not share these
> variables directly.
>
> The runner runs the test suite before merging a plan's work. The suite failed on that random test,
> so the runner refused to merge, and the plan stayed in `pending/`. The six plans that depend on it
> wait for it to reach `executed/`, so none of them ran.
