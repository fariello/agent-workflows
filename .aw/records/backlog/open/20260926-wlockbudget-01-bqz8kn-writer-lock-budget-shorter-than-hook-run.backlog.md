- Id: bqz8kn
- Status: open
- Blocks-Release: next
- Set: wlockbudget
- Priority: medium
- Work-Kind: bug
- Summary: commit_lock.writer_lock waits only 5s and claims holders keep the lock 'well under a second', but holders keep it for a whole pre-commit run (10.6s measured), so a verb's wait can expire and commit unserialized

## Workflow history
- 2026-09-26 created (aw backlog): Split out of duac3v when it graduated to plan y2vzit (finlockwait-01), which deliberately does not change this shared budget.

MEASURED 2026-09-26: 'pre-commit run --files <one review record>' took 10.6s real. commit_lock.writer_lock holds the shared writer lock (the same file as the ipd finalize lock) across that whole window by design (its MEASURED HARM 2026-09-06 comment), yet its docstring says a self-commit holds it 'for well under a second' and its default timeout is 5s. With required=False (the default, used by git_commit_helper.offer_commit) an expired wait PROCEEDS UNSERIALIZED, which re-opens the pre-commit stash race the lock exists to close. User-perceptible: a peer's self-commit can destroy an uncommitted edit in a shared checkout. Fix to decide: raise the budget (trade-off: a stuck lock surfaces more slowly), and correct the docstring. Plan y2vzit handles the finalize side of the same lock.
