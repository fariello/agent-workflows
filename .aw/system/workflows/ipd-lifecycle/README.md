# ipd-lifecycle

The authoritative gate for BEGINNING execution of an approved IPD and for performing its TERMINAL
lifecycle transition. It is the execution-and-transition sibling of `plan-review` (before building)
and `verify-execution` (after building): this one gates the moments IN BETWEEN, deterministically.

At each checkpoint it runs the structural linter `aw ipd lint` and fails closed:

- `--phase pre-execution` at execution start (proceed only on exit 0 + `conforming`);
- `--phase pre-transition` before the terminal transaction;
- `--phase post-transition` on the moved file after the path-scoped lifecycle commit.

Exit `1` is a structural finding to repair; exit `2` (the linter could not run) is a hard stop, not
a skip; `quarantined`/`legacy` are not `conforming` and do not authorize execution. The terminal
transaction (workflow-history line, terminal `Status:`, `git mv` to the terminal directory,
path-scoped commit) is a POST-gate transaction, never an `E-*`/`V-*` checklist item. The linter
proves structure and state only; it never establishes semantic correctness.

Run `/ipd-lifecycle <approved-plan-path>`, or from any agent: "read and execute
`.agents/workflows/ipd-lifecycle/ipd-lifecycle.md`" against a named approved plan.
