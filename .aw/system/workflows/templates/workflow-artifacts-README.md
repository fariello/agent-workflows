# Workflow run scratch

This directory holds the working material of agent-workflow runs: the run records,
verification evidence, and session logs a workflow writes as it goes, under
`<workflow>/<RUN_ID>/`.

## Git Guidelines

**Run scratch is local to this machine and is never committed.** The framework-owned
`.aw/.gitignore` ignores this tree with the anchored pattern `/workflow-artifacts/`
(patterns in that file are `.aw/`-relative, so it resolves to `.aw/workflow-artifacts/`
exactly). Verify that yourself rather than trusting this sentence:

```sh
git check-ignore -v .aw/workflow-artifacts/
```

**Why, because this is a containment rule and not tidiness:** a run record carries local
context, including absolute home paths, usernames, and session detail. Git history is
permanent, so committing one publishes machine identity into it unrecoverably. That is why
the ignore rule should be left alone: do not remove it, and do not force-add a path under
here.

Because this tree is untracked, treat its contents as disposable working material. Nothing
here survives a fresh clone.

## Where durable review history goes instead

Run scratch is the material that PRODUCED a review, not the review itself. Durable history
is a typed, committed artifact under `.aw/records/`:

- `.aw/records/reviews/` holds typed `<...>.review.md` findings records: what a review
  actually found, with severities that tooling can read.
- `.aw/records/plans/` holds the Implementation Plan Documents a review approves, through
  their lifecycle.

So if you want a run's conclusion to outlive this machine, write it as a record under
`.aw/records/`. Do not start tracking this directory.
