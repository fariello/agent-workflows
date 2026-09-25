- Id: h2mpru
- Status: graduated
- Graduated-To: isoperact
- Set: h2mpru
- Priority: low
- Work-Kind: feature
- Summary: worktree isolation is one all-or-nothing run flag; make it configurable per action type (execute / review / orchestrate) and consider sparse checkouts for very large repositories

## Workflow history
- 2026-09-25 graduated (aw set): graduated into isoperact plan bzlxn0 (execute and review; orchestrate is always isolated)
- 2026-09-13 created (aw backlog): worktree isolation is one all-or-nothing run flag; make it configurable per action type (execute / review / orchestrate) and consider sparse checkouts for very large repositories

## What exists today

Isolation is already a run option, but a single all-or-nothing one. `--no-isolate-worktree` is registered
with `default=True` (`oc_runipd.py:7887-7896`), stored in run options (`:3048`), and read at the launch
site (`:6106`, `isolate = state.get("options", {}).get("isolate_worktree", True)`). So the plumbing for a
configuration value already exists; what does not exist is any way to say "isolate execute turns but not
review turns", or to set a default outside the command line.

Set `dirtygates` (orchestrator `8lfoum`) extends isolation to the remaining actors: Order 04 (`u23gbn`)
puts orchestrator retirement in a coordinator-owned throwaway worktree, and Order 05 (`ajxr5d`) isolates
review turns. Once those land, three distinct action types each allocate a worktree, and a single flag
governs all of them.

## Why per-type control is worth having

- The three action types have very different cost/benefit profiles. An execute turn produces commits worth
  protecting; a review turn produces two small files and is cheap to re-run (recorded as F-6 in `ajxr5d`).
  An operator may reasonably want one isolated and not the other.
- A constrained environment (small CI runner, limited disk) may need to disable isolation selectively
  rather than losing it entirely for execute turns, which is where it matters most.
- The orchestrator plan's own OQ-01 asks whether isolation should become MANDATORY. That question is easier
  to answer once the configuration surface is explicit rather than implied by one boolean.

## Measured cost, so the trade is quantified rather than argued

Measured 2026-09-13 on this machine, comparing this repository against a purpose-built large one (300
files of 5MB incompressible random data, roughly 1.5GB):

| | this repo (99M `.git`, 2151 tracked files) | ~1.5GB repo |
|---|---|---|
| `git worktree add` wall time | 0.31s | 1.59s |
| worktree disk | 46M | 1.5G |
| per-worktree git metadata | 344K | 52K |

Conclusions from those numbers:

- TIME IS NOT THE PROBLEM. 1.59s on a 1.5GB repository, because a worktree writes files rather than
  copying history, and shares the object store through a `gitdir:` pointer (metadata was 52K).
- DISK IS THE PROBLEM, AND IT IS LINEAR IN PARALLELISM. Each worktree materializes a full checkout, so
  three concurrent lanes on a 2GB repository is roughly 6GB of transient disk.

Two mitigations were verified to WORK mechanically (not verified to be SAFE for a real build):

- `git worktree add --no-checkout` produced an 8.0K worktree, effectively instant.
- `git sparse-checkout init --cone` plus a path set materializes only the selected paths. Every plan
  already declares `- Scope-Paths:`, so a sparse worktree containing those paths plus the test surface is
  a plausible design. THE RISK IS EXPLICIT: a build or test that reads a file the plan never declared
  would fail confusingly, and `Scope-Paths` is a declaration rather than an enforced boundary. Any sparse
  design must decide what happens when an undeclared path is read.

HONEST LIMIT OF THE MEASUREMENT: the large fixture used incompressible random data, which is the worst
case for git's delta compression and not typical of a 2GB source repository. A real one would have a
smaller `.git`, though the CHECKOUT size (the cost that matters here) would be comparable.

## Suggested shape

1. Accept a per-action isolation setting (execute / review / orchestrate), defaulting all three to
   isolated so current behavior is unchanged.
2. Allow it in configuration, not only as a command-line flag, so an operator on a constrained machine
   does not have to remember a flag on every invocation.
3. Keep `--no-isolate-worktree` working as a shorthand for all three, so no existing invocation breaks.
4. Optionally investigate sparse checkouts for large repositories, with the undeclared-path question
   answered before anything ships.

## Why this is low priority and not blocking

The `dirtygates` Set achieves its goal (nothing writes to the shared checkout mid-run) with isolation on
by default for every action type, and this repository's measured cost is negligible: 0.31s and 46M per
worktree. This item matters only for a much larger repository or a disk-constrained host, neither of which
is the current situation. Filed so the design question is recorded rather than rediscovered.

## Related

- Plan Set `dirtygates` (orchestrator `8lfoum`), especially Order 04 (`u23gbn`) and Order 05 (`ajxr5d`),
  which are what make three action types allocate worktrees.
- The orchestrator's OQ-01 (should isolation be mandatory), which this item informs.
