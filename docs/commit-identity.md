# Commit Identity and Agent Trailers

Every commit and merge that `aw` creates keeps the human operator as the Git author and records an agent committer identity alongside structured Git trailers. Plain `git commit` invocations made directly by the operator outside `aw` are untouched.

## Author and committer fields

When `aw` creates a commit or merge commit, it leaves `GIT_AUTHOR_NAME` and `GIT_AUTHOR_EMAIL` unset so Git uses the repository's normal user identity (`user.name` and `user.email`) as the author.

For the committer identity, `aw` sets:

- `GIT_COMMITTER_NAME`: `AW Agent (<model>)`, where `<model>` is the resolved model for the run (`options["model"]`) or the value of `AW_AGENT_MODEL` in the environment, and `unknown` when neither is set.
- `GIT_COMMITTER_EMAIL`: the user's own email address with `+aw` inserted before the `@` (for example, `you@example.com` becomes `you+aw@example.com`). If the local part already carries a `+` tag, `-aw` is appended to the existing tag (for example, `you+dev@example.com` becomes `you+dev-aw@example.com`).

If no user email is configured or the configured value contains no `@`, `aw` sets no committer override and lets Git behave as usual.

When `commit.gpgsign` is enabled and `user.signingkey` is not explicitly configured, Git normally selects a signing key using the committer identity. To keep commit signing working without extra setup, `aw` supplies `user.signingkey` via a transient `GIT_CONFIG_*` environment override set to the author's `Name <you@example.com>` identity whenever `commit.gpgsign` is `true` and `user.signingkey` is unset.

## Trailers

Commits and merges created by `aw` carry up to three structured trailers at the end of the commit message:

- `AW-Runner: <runner>`: present when the runner is known (`aw oc run`, `aw agy run`, or `aw commit`). Other `aw` verbs run outside a runner (such as `aw ipd set --commit`) record the agent committer identity without inventing an `AW-Runner` trailer.
- `AW-Run: <run-id>`: the run identifier (`run-YYYYMMDDTHHMMSSZ-<pid>`) when the commit is produced inside or on behalf of an `aw` run.
- `AW-Item: <id6>`: the 6-character plan, spec, or backlog identifier when the commit is bound to a specific work item.

Each trailer key is added at most once per commit message.

## Filtering and inspecting history

List commits made through `aw`:

```sh
git log --committer='AW Agent'
```

Inspect author, committer, and runner trailer side by side:

```sh
git log --format='%h %an | %cn %(trailers:key=AW-Runner,valueonly)'
```

Filter commits by a specific runner surface:

```sh
git log --grep='^AW-Runner: aw oc run$'
```

## Scope and limits

This mechanism is an attribution and audit label, not a security boundary:

- Inside an `aw oc run` or `aw agy run` agent turn, the runner exports `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`, `AW_AGENT_MODEL`, and `AW_RUNNER` into the child environment, so both `aw commit` and a plain `git commit` run by the agent in its lane receive the agent committer identity.
- Outside a managed run, a local process with shell access can still run raw `git commit` with arbitrary environment variables. Separating credentials or enforcing identity at the OS boundary requires a distinct OS account or external repository hosting controls.
