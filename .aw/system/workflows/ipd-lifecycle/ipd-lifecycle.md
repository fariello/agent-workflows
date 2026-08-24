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
