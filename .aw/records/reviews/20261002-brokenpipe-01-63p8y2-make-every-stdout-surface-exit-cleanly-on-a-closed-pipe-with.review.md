# Review findings: plan 63p8y2

- Subject-Id: 63p8y2
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `1e73f8468`. The plan was committed and unchanged, so no
snapshot was taken. `aw ipd lint --phase author` was clean. `--phase review-finalize` was clean apart
from `IPD-M107`, which clears when the review history line is written. `- Kind: child`.

Re-verified: `cli.main`'s `try`/`except KeyboardInterrupt`/`except EOFError`/`finally` shape and its
four restorations. All three console scripts map to `agent_workflows.cli:main`, and `__main__`
calls `main()`. `renderers.BaseRenderer.emit` catches `(BrokenPipeError, OSError)`. Section 7 still
reads "All handlers catch". Section 3 holds the three-state vocabulary. Backlog `kinyxf` is
`Work-Kind: bug` with `Blocks-Release: next`, which the plan inherits. Sibling `okiso1` exists. The
plan's prototype reproduced F-09 on `attention` (1, flush path) and `find plans` (0, dispatch path),
deterministically over repeated runs.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A / Section 4 anti-greenwashing | Prototype: `aw attention --all` exits 1 unpiped but 0 piped into `head -1`, failing inside `_dispatch` | OQ-02, E-04, V-04 and the Section 7 wording all claim the asymmetric design preserves a command's genuine verdict. That holds only when the verdict is computed before the write fails. A streaming command with live findings is reported 0. V-04's "no surface with genuine findings returns 0" is false. | all Low | FIXED | Design kept (no honest better code exists for an uncomputed verdict), but E-04, E-05, OQ-02 and V-04 now state the limit and demonstrate both cases. F-12 added. |
| PR-002 | HIGH | UNDER-SCOPE | A (coverage of the fix) | Closed-pipe harness: the prototype still exits 120 for `aw --help` and `aw find --help`; adding a flush on `except SystemExit: ...; raise` gives 0, and `aw nosuchverb` keeps 2 | argparse leaves `_dispatch` via `SystemExit`, so the post-return flush never runs and every `--help` surface stays broken. | all Low | FIXED | E-02 adds the guarded flush plus re-raise on `SystemExit`. E-01 covers `--help`. V-02 demands it. F-11 added. |
| PR-003 | MEDIUM | IN-SCOPE | E (determinism; suite contract) | `pytest_timeout` not importable; `doctor` about 54 s unpiped; `attention` about 17 s piped; `pyproject.toml` `slow` marker for subprocess-heavy files | The harness ("read one or two lines, then close") is timing-dependent. The plan's `@pytest.mark.timeout` is inert here. Unmarked subprocess tests of about a minute would land in the fast default suite. | all Low | FIXED | E-01 now closes the read end BEFORE launch (deterministic EPIPE, measured), marks the module `slow`, and runs it with `-m slow` in V-01/V-03/V-06. |
| PR-004 | MEDIUM | IN-SCOPE | E (evidence feasibility) | `aw find plans --json >/dev/full` exits 0 with no error; `aw check plans --json >/dev/full` exits 1 with no `No space`; `aw find plans >/dev/full` exits 120 with `No space` | The ENOSPC probe would falsely fail on a renderer surface, whose broad `OSError` catch already swallows ENOSPC. | all Low | FIXED | Probe pinned to a non-renderer surface. F-13 added. The renderer gap is recorded in Deferred. |
| PR-005 | LOW | IN-SCOPE | G (execution contract) | Gate POST-GATE paragraph; OQ `Owner: none` | Lifecycle ownership was unconditional, there was no fence declaration, and self-resolved questions had no owner. | all Low | FIXED | Added conditional ownership and a declaration-style fence. Owners set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep returning 0 on a mid-dispatch broken pipe, given it can hide findings? | Keep 0, document the limit in Section 7 and at the site. | Return 1 (asserts findings never measured); return 2 (asserts cannot-run when the command ran); force a pre-computed verdict (requires restructuring every command, out of scope). | F-12 measurement; Section 3 meanings of 1 and 2. | yes |
| D-2 | Handle the `SystemExit` path? | Guarded flush, then re-raise the same `SystemExit`. | Leave it (all `--help` surfaces stay at 120). | F-11 probe. | yes |
| D-3 | How to make the harness deterministic? | Close the read end before launching the child; mark the module `slow`. | Read-then-close (timing-dependent); sleeps/retries (the plan itself forbids them). | Review probe reproducing 120 on five surfaces. | yes |
