- Id: 3sh9d6
- Status: done
- Graduated-To: 3sh9d6
- Set: 3sh9d6
- Priority: medium
- Work-Kind: chore
- Summary: The published `docs/cli-output-contract.md` non-TTY retraction is correct but plan 9iiqmm and its review both recorded the OPPOSITE as measured fact, so two artifacts assert a behavior that does not exist

## Workflow history
- 2026-09-30 set (aw backlog): closed by aw oc run: IPD dv7c49 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260928-3sh9d6-01-dv7c49-correct-9iiqmm-s-falsified-non-tty-claims-by-appended-note-a.ipd.md); evidence .aw/records/plans/executed/20260928-3sh9d6-01-dv7c49-correct-9iiqmm-s-falsified-non-tty-claims-by-appended-note-a.ipd.md
- 2026-09-30 note (aw backlog): Execution under plan dv7c49 departed from the item's literal FIX in two ways: first, F-12, under-scope, and OQ-04 were corrected by appended history records (in 9iiqmm and Round 2 of its review) rather than in-place rewriting, which AGENTS.md forbids on executed plans and which would overwrite measured review evidence; second, the diagnosis was incomplete because the feature never shipped on main, so the lost code and recovery shas were filed and tracked under backlog an77ub.
- 2026-09-28 set (aw backlog): graduated by run run-20260928T235941Z-1396311: dv7c49
- 2026-09-20 created (aw backlog): Found while executing 9iiqmm: the plan's F-12, its under-scope, and OQ-04 all state (as MEASURED) that select_output routes to AGENT mode on any non-TTY stdout. It does not, and never did; that promise was retracted 2026-09-19 in docs/cli-output-contract.md Section 9.

MEASURED in lane worktree `9iiqmm` at base bb714fd8:

    $ python3 -m agent_workflows attention --dir <tmp-repo> | cat
    ## ready (1)
    - [plans] .agents/plans/pending/20260920-demo-01-aaa111-demo.md (draft)
    TODO: 4 files waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.

i.e. a PIPED invocation renders the HUMAN BOARD, footer line included. `select_output` (`result_types.py`) consults `stdout.isatty()` for COLOR only, and its own docstring now says so explicitly: 'THIS DOCSTRING USED TO CLAIM that non-TTY stdout selects AGENT mode ... NEITHER WAS EVER IMPLEMENTED'. `docs/cli-output-contract.md` Section 9 records the retraction (maintainer ruling, ttyflags `yaxr4i` OQ-01, 2026-09-10).

WHERE THE STALE CLAIM LIVES, all in plan `9iiqmm` (`.aw/records/plans/.../20260908-awinbox-02-9iiqmm-...ipd.md`):
  - F-12, rated HIGH, whose Evidence column reads 'source read; ran it': 'THE LINE REACHES AN INTERACTIVE TERMINAL AND NOTHING ELSE, INCLUDING NO PIPE.'
  - the `## Scope check` under-scope paragraph: 'ANY PIPED OR REDIRECTED invocation all show nothing'.
  - OQ-04's rationale, which costs three routes on the premise that agents cannot see the line.
  - the same claim in the plan's `## Workflow history` review note (PR-602) and in its typed review record under `.aw/records/reviews/`.
The plan's E-02 instruction was still followed to the letter (independent `if`, no `Drift`, no JSON key), so no CODE is wrong; what is wrong is a durable assertion about runtime behavior, recorded as measured, that a later reader will trust.

WHY IT MATTERS RATHER THAN BEING A TYPO. The claim was load-bearing for a DESIGN DECISION: OQ-04 exists only because agents were believed blind to the nudge, and a future reader of OQ-04 could spend a round of work 'fixing' invisibility that is not there. It also mis-states the feature's reach to whoever reviews it next.

NOTE the OQ-04 finding it cites is INDEPENDENT and still true: `to_agent_record` derives `findings` from `len(diagnostics)` with no severity filter, so a WARNING diagnostic would read `findings: 1` on a clean repo. That part needs no correction.

FIX: correct F-12, the under-scope paragraph, and OQ-04 in the plan (and the review record) to state that the line renders on the human board including a PIPED invocation, and that it is absent only under `--agent`, `--json`/`--format json`, `--check`, and the `--id6-only`/`--paths`/`--filenames` early return. Since `9iiqmm` is being executed now, the correction belongs in a follow-up edit rather than in-place rewriting of an executed plan's findings.
