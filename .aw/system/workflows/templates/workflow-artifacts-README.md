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

Because this tree is untracked, treat its contents as disposable working material, with the exception of runs whose workflow calls their record a durable output (such as an assess run where no IPD was created, or an in-progress release-review run). Nothing
here survives a fresh clone.

## Reclaiming space

To preview and prune aged runs, run:

```sh
aw archive workflow-artifacts
```

By default this previews deletions without modifying disk. To permanently delete candidate runs, re-run with:

```sh
aw archive workflow-artifacts --apply
```

The prune rule keeps the newest 5 runs per workflow and any run younger than 30 days. Runs with unresolved questions, unreviewed decisions, unfinished release reviews, or runs that represent a sole durable output are always kept regardless of age. Deletion is permanent because the tree is untracked.


## Where durable review history goes instead

Run scratch is the material that PRODUCED a review, not the review itself. Durable history
is a typed, committed artifact under `.aw/records/`:

- `.aw/records/reviews/` holds typed `<...>.review.md` findings records: what a review
  actually found, with severities that tooling can read.
- `.aw/records/plans/` holds the Implementation Plan Documents a review approves, through
  their lifecycle.

So if you want a run's conclusion to outlive this machine, write it as a record under
`.aw/records/`. Do not start tracking this directory.
