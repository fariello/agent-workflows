- Id: bxi1o0
- Status: graduated
- Graduated-To: bklgdryrun
- Blocks-Release: next
- Set: bklgdryrun
- Priority: high
- Work-Kind: bug
- Summary: aw backlog set and aw specs set IGNORE --dry-run on their --status spelling: the backlog one rewrites the record and the specs one MOVES it between disposition directories, both reporting success

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set bklgdryrun (commit 2c7068ca).
- 2026-09-25 created (aw backlog): aw backlog set --dry-run silently WRITES when the --status spelling is used: backlog.run_set never reads dry_run, so a preview mutates the file and reports success

## How it was found (a live incident in a shared checkout, not a lab exercise)

Hit on 2026-09-25 during `/plan-review` of plan `6k7xot`, while verifying a remediation shape that
plan recommends. The review ran what it believed was a READ-ONLY preview against a real tracked
record in a shared worktree:

```sh
aw backlog set .aw/records/backlog/open/20260910-bklghist-01-hg2oop-....backlog.md \
  --status open --blocks-release next --dry-run
```

`git status` afterwards showed that record MODIFIED, with a history line appended. The review noticed
it only because it inspects the staged set before committing, per the AGENTS.md shared-checkout rule,
and reverted it with `git restore`. Nothing was committed and nothing was lost.

THAT IS THE REAL SEVERITY. An agent that trusts `--dry-run` and commits without diffing would have
committed a mutation to a record it never intended to touch, in a checkout other agents and humans
are working in concurrently. This is exactly the class of loss the shared-checkout rules exist to
prevent, and it is reachable through a flag whose entire purpose is to not write.

## The defect

`aw backlog set` has TWO spellings that route to DIFFERENT implementations (see `cli.py`, the
`backlog_command == "set"` branch): the POSITIONAL form routes to `status_set.run_set_command`, and
the `--status` form routes to `backlog.run_set`. `backlog.run_set` never reads `dry_run` at all
(`grep -n dry_run agent_workflows/backlog.py` returns nothing), so the flag is accepted by argparse,
silently ignored, and the write proceeds.

## Reproduction (measured 2026-09-25, isolated scratch repo)

One item, status `open`, set to `open` again with `--dry-run`:

```text
A  --status spelling   exit 0  | wrote? True      <- ignores --dry-run
B  positional          exit 0  | wrote? False     <- honors --dry-run
```

The `--status` run also reordered front-matter bullets (`- Order:`/`- Priority:` swapped) and appended
`- 2026-09-25 set (aw backlog): status -> open`, i.e. it performed the full re-render.

## Why this is HIGH and gates the release

An ignored `--dry-run` is worse than a missing one: a missing flag refuses and teaches, while an
ignored one performs the mutation and reports success, so the operator's own verification step is the
thing that fails. It is also user-perceptible by the AGENTS.md test (a wrong outcome, not merely a
slow one), and it silently mutates tracked records in a shared checkout.

## Suggested fix

Honor `dry_run` in `backlog.run_set`: compute the rendered result, print the would-write preview in the
same shape the positional path prints, and return 0 WITHOUT writing. Then close the fork properly, in
one of two ways (decide, do not assume):

1. Make the two spellings share one implementation, so no flag can be honored by one and ignored by
   the other. Preferred, and it removes the whole class.
2. Keep the fork and add a contract test asserting that EVERY flag both spellings accept has the same
   effect, `--dry-run` included.

## Verification this needs

1. `--status` spelling with `--dry-run` leaves the file byte-identical and exits 0.
2. The positional spelling keeps its current correct behavior (regression guard).
3. A test asserting the two spellings agree on `--dry-run`, so the fork cannot silently re-diverge.
4. The sibling `aw specs set` has the SAME defect and it is WORSE. Measured 2026-09-25, same method:

   ```text
   $ aw specs set <path> --status to-review --dry-run
   exit 0
   aw specs set: .../specs/to-review/20260908-aaa111-01-aaa111-x.spec.md -> to-review
   BEFORE: ['.aw/records/specs/20260908-aaa111-01-aaa111-x.spec.md']
   AFTER : ['.aw/records/specs/to-review/20260908-aaa111-01-aaa111-x.spec.md']
   git status:  D .aw/records/specs/20260908-...spec.md
                ?? .aw/records/specs/to-review/
   ```

   A `--dry-run` MOVED THE FILE BETWEEN DISPOSITION DIRECTORIES and reported the destination path as
   though it were describing a preview. It also created an untracked `.aw/records/history.jsonl`. So
   the fix must cover both setters, and the shared-implementation option (1) is the stronger choice
   precisely because this bug has already been duplicated once.
