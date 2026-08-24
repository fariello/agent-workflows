# IPD lifecycle (authoritative execution and terminal-transition path)

Treat this file as the controlling instruction for BEGINNING execution of an approved IPD and for
performing its TERMINAL lifecycle transition. It is the single authoritative gate for both moments.
It exists because the repository has no other general execution/transition workflow: `verify-execution`
is POST-execution only (it cross-checks an already-executed plan and never gates pre-execution or
pre-transition). This workflow closes that gap (spec `.aw/records/specs/20260802-1904-01-ipd-structure-and-linting.spec.md`, Sections 11 and 12.1).

The deterministic structural linter `aw ipd lint` is the gate at every checkpoint. It proves
STRUCTURE and STATE only; it never establishes semantic correctness, coverage, evidence
sufficiency, or truthful classification. Semantic judgment (did the work actually happen, is the
pasted evidence real) remains the executor's and reviewer's responsibility.

## Preconditions (before execution may start)

1. The controlling SPEC (if the plan implements one) is formally approved by the human maintainer.
2. The PLAN is `Status: approved` (a human sign-off recorded in its `Approval:` metadata) or, for a
   low-complexity mechanical corrective, `auto-approved` per the repository's rules. Neither this
   workflow nor any agent may self-approve a plan it authored.
3. If either is missing, STOP and report; do not begin execution.

> Scope of `STOP and report` (additive clarification; execset Order 02): when a single IPD is run on
> its own, `STOP and report` means what it always has - halt and surface the situation to the human.
> When the same IPD runs as a CHILD under a Set coordinator (`aw ipd execute-set`), a child's `STOP
> and report` is CHILD-scoped: it returns control to the Set coordinator, which applies the exact
> two-condition stop rule (`hard_stop = needs_human AND no_robust_decision AND cannot_defer_subgraph
> AND cannot_defer_ipd`) after draining independent work, rather than terminating the whole Set. This
> is backward compatible: nothing changes for non-Set execution.

## Checkpoint 1: pre-execution gate

Run, on the plan file:

    aw ipd lint --phase pre-execution --agent <plan-file>

Proceed to execute ONLY when the process exits `0` AND the disposition is `conforming`.

### `aw ipd begin`: the durable, fail-closed start receipt

`aw ipd begin <plan> --actor <agent/model>` is the authoritative single-IPD execution entry. It runs
the `pre-execution` gate above and, on conformance, FREEZES the plan's requirements and `Scope-Paths`
and writes a LOCAL, gitignored receipt under `.aw/state/ipd-lifecycle/<id6>.receipt.json` binding
`{plan Id, plan content digest, frozen requirement/scope digest, base HEAD, actor/model, timestamp}`.
This is the durable proof - retained even after the fact - that the approved plan and its scope passed
the gate at a specific base HEAD, which Order 04's `aw ipd finalize` later requires.

It is fail-closed: a non-conforming lint (exit 1), an unrunnable lint / missing `--actor` /
dirty-or-ambiguous baseline / unresolvable-or-ambiguous plan selector / interrupted write (exit 2) all
leave NO valid receipt and therefore NO execution authority. The receipt is written atomically (an
interrupted write never leaves a partial receipt) and is resumable (a re-read returns the same
receipt). It PERSISTS across unrelated intervening commits on disjoint paths (HEAD movement alone does
not invalidate it, preserving a concurrent multi-agent workflow); it is invalidated only by a change
to the plan's own content digest or an intervening commit that touched a path inside the plan's
`Scope-Paths` (that path-overlap collision is enforced by `aw ipd finalize`, Order 04). It mutates no
tracked file and the receipt is never committed.

Fail-closed rules (identical at every checkpoint here):

- Exit `1` (a conformance error): a STRUCTURAL finding to repair; do NOT proceed. Fix the plan (or
  emit a corrective), re-run, and only then continue.
- Exit `2` (the linter could not run: invocation, parser, or internal failure): a HARD STOP. The
  tool being unable to run is never treated as a pass or a skip.
- A `quarantined` or `legacy/not evaluated` disposition is NOT `conforming` and does NOT authorize
  execution, even though the process exit is `0`.

## Execute

Execute the plan's `## Detailed Implementation Checklist (TODO)` items in dependency order. Mark an
`E-*` item `- [x]` with `Execution state: performed` ONLY after performing the action (that mark is
NOT validation). Then complete the `## Validation and cross-check` pass: for each `V-NN`, inspect
independently checkable evidence, fill `Observed evidence:`, and set `Result: pass` only when the
evidence supports the expected outcome. Commit the plan's PRODUCT changes path-scoped as you go
(never `git add -A`/`-a`; never push). The terminal lifecycle transition is NOT one of these
checklist items; it happens only at Checkpoint 2 below.

## Checkpoint 2: pre-transition gate

When every `E-*` is `performed`+checked and every `V-*` is `pass`+checked with nonempty observed
evidence, run:

    aw ipd lint --phase pre-transition --agent <plan-file>

Perform the terminal transaction below ONLY on exit `0` + `conforming`; otherwise apply the same
fail-closed rules (exit 1 = repair, exit 2 = hard stop).

### `aw ipd finalize`: the atomic terminal transaction

`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` performs the entire
terminal transaction below as ONE scope-checked, evidenced command. It validates the matching
`aw ipd begin` receipt (refusing if absent or stale), runs `pre-transition` lint, then compares the
paths this execution changed SINCE the receipt's frozen base HEAD against the reviewed `Scope-Paths`:
it REFUSES (plan left unmoved) on any unexplained path outside `Scope-Paths` (the exact p7dqwz
signature: an extra `tests/test_empty_state_ux.py`), and computes+surfaces the in-scope
intervening-commit set as evidence (authorship-aware collision enforcement is the rollback order's
adversarial surface). On a clean in-scope precheck it appends the attributed `<agent/model>` history
entry (never a generic actor), sets terminal status, moves the plan, refreshes the owned plans index
FAIL-LOUD (a failed refresh aborts the transaction, never a silent stale index), creates the
path-scoped lifecycle commit (only the plan file + the owned index), runs `post-transition` lint, and
reports the commit hash plus the captured pre-execution/pre-transition/post-transition gate evidence.
Preview by default; `--apply` performs the transition. Exit 0 = finalized, 1 = refusal (gate/scope),
2 = cannot run. This is the ONLY supported terminal path; the manual ordered steps below are the
contract it implements.

No ungated bypass (Order wezhxg): the raw `aw set executed <plan>` / `aw ipd set executed <plan>` (and
the `done` alias) no longer perform an ungated move - they TRANSPARENTLY DELEGATE into this gated
`aw ipd finalize` transaction (keyed on the artifact being a plan and the target being `executed`), so
`executed` is unreachable without the receipt, scope reconciliation, three gates, attributed history,
and lifecycle commit. They require an attributed `--actor <agent/model>`; a missing actor fails closed
naming the exact command (never a fabricated generic actor, never a bare dead-end). Plan RETIREMENT
(`superseded`/`not-executed`) keeps its separate `RETIRED ...` header + `git mv` flow (finalize does
not perform retirement), and every non-plan artifact terminal transition (prompt/spec/backlog/release)
plus every nonterminal plan transition is unchanged. The post-transition attribution lint additionally
rejects a generic (`aw set`)/empty actor or empty summary on the newest terminal history entry,
forward-only (the existing executed tree is grandfathered via Order oorry1's `Scope-Paths` cutoff).

Local commit gate (Order dulzpy, defense-in-depth for the raw-commit path): Order wezhxg's delegation
covers the CLI, but an agent that never touches the CLI can still hand-edit a plan's `- Status:` to
`executed` (or `git mv` it into `executed/`) and `git commit` it raw, running no finalize. A LOCAL
`repo: local` pre-commit hook (`python3 -m agent_workflows ipd-executed-gate`, installed into
`.pre-commit-config.yaml` by `aw install`/`setup-repo`) inspects the staged diff and, for each PLAN
gaining `- Status: executed`/`done` or moved into `executed/`, requires matching finalize evidence in
`.aw/state/` (the finalize transaction journal proving `aw ipd finalize` performed THIS transition);
absent evidence REFUSES the commit naming `aw ipd finalize <plan>`. Honest limits: git hooks are LOCAL,
not cloned by default, and skippable with `--no-verify`, so this is PREVENTION, not an absolute gate;
the deterministic backstop is the `proclint` detector via `aw check`/`aw doctor`. There is deliberately
NO remote/CI enforcement. It does NOT fire on prompts (which share the `executed` token), non-plan
artifacts, nonterminal plan changes, or ordinary commits.

Untooled INTERMEDIATE status detector (proclint Order 79li67, the sibling of Order dulzpy): the dulzpy
gate covers the TERMINAL `->executed` commit, but nothing catches a hand-edited INTERMEDIATE transition
(`draft`->`to-review`->`reviewed`->`approved`, and `approved` is a trust boundary). Lifecycle status is
meant to change via `aw set`/`aw ipd set`, which append an attributed `- <date> <status> (<actor>): <msg>`
line to `## Workflow history` on every transition; a hand-edited `- Status:` produces no such line. A
COMMIT-SCOPED detector (`check.status-untooled`) compares the STAGED plan content against HEAD and flags
each plan whose `- Status:` changed in this commit with NO matching tool-authored history line for the new
status, surfaced BOTH through `aw check`/`aw doctor` (over changed files - a fast no-op when nothing is
staged) AND, primarily, a LOCAL `repo: local` pre-commit hook (`python3 -m agent_workflows
ipd-status-untooled-gate`, installed into `.pre-commit-config.yaml` by `aw install`/`setup-repo`) that
refuses the commit naming `aw set <status> <id6>`. It is commit-scoped: only files changed in the commit
are examined (so historical records are NEVER scanned - no grandfathering), `executed/` records are
excluded (terminal; a move OUT of `executed/` is a staged change and IS checked), and history-less types
(prompts/releases carry no `## Workflow history`) are excluded. Honest limits: this is predicate A
(textual) - it catches the CARELESS omission (a status flip with no note) but is EVADABLE by a hand-edit
that also writes a plausible line, and `--no-verify` bypasses the hook; it is a safety net, not a proof
(the preventive layer is the `aw set` delegation + the `ipdgates` gates). There is deliberately NO CI.

Recovery paths (no bypass MUST NOT mean no way forward): each stuck case has an honest, non-fabricating
recovery. (1) MISSING begin receipt: finalize refuses and points to running `aw ipd begin` (it does NOT
back-date a start that never happened); a genuinely pre-receipt/grandfathered plan records an honest
retroactive/advisory acknowledgment rather than a false "verified against a receipt". (2) A legitimate
mid-stream out-of-scope edit: light-touch - supply `--scope-reason <path>=<why>` (or widen `Scope-Paths`
and re-review) and proceed; the gate exists to make you NOTICE, not to force a rewrite. (3) Grandfathered
/ no `Scope-Paths`: the scope check is advisory-only, no lockout. finalize is a double-check gate ("did
you do what you said, and only that?"), NOT a correctness oracle: it cannot prove completeness or test
sufficiency - those remain the V-item evidence, a fresh-context verifier, and human review.

Two-way scope reconciliation (DECISIONS.md D141): rather than a bare refusal on any unforeseen edit,
finalize reconciles the scope delta in BOTH directions at this one unskippable step and RECORDS the
answers verbatim into the terminal history (it SURFACES + ATTRIBUTES deviations; it does not judge
their legitimacy). For each path this execution changed that is OUTSIDE the frozen `Scope-Paths`, a
short RECORDED REASON is required (reason given -> record + proceed; empty/missing -> do not finalize).
For each path DECLARED in `Scope-Paths` but NOT modified (the only check that catches MISSING work), a
one-word ACKNOWLEDGMENT is required (e.g. `not-needed`; acknowledge-and-proceed). On a TTY these are
collected in ONE batched prompt; headless (the normal agent context) they are supplied as repeatable
`--scope-reason <path>=<why>` and `--scope-ack <path>[=<note>]` flags. A headless run with a non-empty
delta and MISSING answers FAILS CLOSED (exit 1) naming each unanswered path and the exact
`aw ipd finalize ... --scope-reason/--scope-ack ...` re-invocation - it never hangs on a prompt and
never silently skips. A clean delta (nothing out-of-scope, nothing declared-but-unmodified) is a
frictionless no-op.

Crash-safe two-phase failure semantics (Order 3xh53a): the whole finalize transaction is wrapped in a
durable journal + exclusive writer lock under the gitignored `.aw/state/runtime/` tree (reusing the
`layout_migration.MigrationManager` pattern), with a two-phase boundary at the lifecycle commit. The
journal moves through phases `prepared` -> `mutating` -> `ready-to-commit` -> (`committed-incomplete` |
`complete`), with `unknown-outcome` as a fail-closed terminal-ambiguous state. BEFORE the commit, any
failed or interrupted step (status set, move, index refresh, staging) rolls back idempotently to the
pre-finalize plan bytes/path and the exact prior Git-index entries for lifecycle-owned paths, WITHOUT
touching disjoint dirty or staged work, then regenerates the plans index from the current corpus. A
second finalizer for the same shared manifest fails with an actionable lock-owner/retry diagnostic; a
stale lock (dead PID) is reclaimed after consulting the journal. The commit boundary is classified by
OBSERVED repository state (the lifecycle commit's marker), never by whether the commit subprocess was
merely invoked: HEAD moved via our commit -> `committed-incomplete` until post-transition passes; HEAD
moved otherwise, or a corrupt/missing journal at a partial state -> `unknown-outcome` (fail closed,
never inferred success). A `committed-incomplete` transaction NEVER amends/resets or creates a second
lifecycle commit: re-running the SAME `aw ipd finalize <plan>` (the plan now lives in `executed/`)
resumes by re-running ONLY post-transition validation and marks the receipt + journal complete on
pass; a persistent failure stays `committed-incomplete` and requires a corrective follow-up IPD. Only a
`complete` transaction reports finalize success and consumes the begin receipt. On process restart, a
pre-commit journal is rolled back idempotently before a fresh attempt.

## The terminal transaction (post-gate; ordered, recoverable)

Perform these steps as one finalization transaction, in order:

1. Append the required `## Workflow history` entry (`<date> executed (<agent/model>): ...`).
2. Set the terminal `Status:` (`executed`, or `superseded`/`not-executed` with a `RETIRED ...`
   header).
3. `git mv` the file from `.aw/records/plans/pending/` to the matching terminal directory.
4. Create the path-scoped lifecycle commit (only the plan file and, if not already committed, its
   product changes; never `git add -A`; never push).
5. Run the post-transition check on the MOVED file:

       aw ipd lint --phase post-transition --agent <moved-plan-file>

6. Report the lifecycle commit identifier and any post-transition failure.

Recovery:

- BEFORE the lifecycle commit, any failure MUST leave the plan in its pre-transition directory and
  status with NO partial move; the state is recoverable by re-running after repair.
- AFTER the lifecycle commit, a failing `post-transition` check is reported as INCOMPLETE lifecycle
  finalization and repaired with a corrective follow-up IPD that cites it; it is NEVER reported as a
  successful transition and the completed commit is NOT rewritten.

## Bootstrap exception (narrow, temporary)

The only permitted exception to invoking `aw ipd lint` is the labeled bootstrap exception
(`machine preflight unavailable: bootstrap`), valid SOLELY while the implementation Set that creates
the linter is still creating it. Once `aw ipd lint` exists, the tool being unavailable is exit `2`
and fails closed; there is no permanent prose-only fallback.

## What this workflow is not

- It is not semantic review (`plan-review` before building) and it is not post-execution
  verification (`verify-execution` after building). It gates the BEGINNING of execution and the
  terminal transition, deterministically.
- It never approves a plan or a spec; human approval is a separate, prior step.
- It never creates or pushes a tag, GitHub Release, or registry upload.

## Set coordination contracts (additive; execset Order 03)

When a whole approved Set is run by the coordinator (`aw ipd execute-set`, over the compiled
execution manifest), the following contracts hold ON TOP OF this per-IPD lifecycle. They are additive
and change nothing for single-IPD execution.

- Scheduling: the coordinator composes the run engine's DAG/gate readiness and the concurrency
  analyzer's eligibility to run the maximal PROVABLY-safe wave; it never overrides the analyzer toward
  more concurrency, and every node reaches a recorded disposition (running/deferred/serialized/blocked)
  - none is silently ignored. Uncertain ownership serializes.
- Leases + isolation: every WRITE lane gets a REAL git worktree (under gitignored `.aw/worktrees/`), a
  fresh session, and a per-path EXCLUSIVE lease; a second lane cannot claim a path another lane owns.
  Workers never write coordinator-owned surfaces (`events.jsonl`, source IPDs, history, backlog,
  walkthroughs, the main worktree); the lease + worktree isolation fences them.
- Model roles: each lane is classified `coding | human_prose | mixed | verifier` and routed to an
  operator/host-configured model binding. A missing binding FAILS CLOSED (no silent default). The
  verifier lane is always a fresh context.
- Decision handshake: a worker mutation is permitted only AFTER the coordinator durably records an
  authorization (write-ahead `decision_proposal -> coordinator record -> decision_authorized`); a
  consultation-preferred choice pauses as a proposal until the coordinator records its disposition.
- Integration + revalidation: returned path-scoped commits integrate in topological/IPD/lane order
  through the merge-and-revalidate gate, which reruns validation on the COMBINED HEAD (per-lane green
  never implies integrated green) and rejects on conflict/overlap/scope-violation/stale-base.
- Recovery + honesty: restart reconstructs lease/node state without replaying completed side effects
  (fail-closed on unknown outcomes); evidence bound to a pre-integration HEAD is invalidated before it
  can satisfy a terminal transition; deferred IPDs remain pending (never marked executed); a Set is
  `set_complete` only when every required child reached verified terminal lifecycle.
