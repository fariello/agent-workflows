# Review: Decouple self-finalize from the verifier turn and earn integration with a driver-run suite

- Plan-Id: evgi9n
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `fbc8b32d`, working tree clean, target plan committed and unchanged.
Structural preflight `aw ipd lint --phase author` reports `conforming`.

SELF-REVIEW DISCLOSURE: I authored this plan earlier in this same session. That makes an
independent-reviewer stance impossible, so I reviewed it by attacking the assumptions I never MEASURED
when writing it, rather than by re-reading my own reasoning. That approach found one BLOCKER I had
missed, which is the justification for doing the pass at all instead of going straight to
implementation. A maintainer should weigh this verdict accordingly: it is a self-check, not an
independent review.

The plan's central diagnosis re-verified TRUE: `--validate` defaults False, `--no-self-finalize`
defaults True, `verify_disp` is assigned in 6 places ALL inside the validate-guarded block, and the
gate at `oc_runipd.py:4984` requires `verify_disp == "verified"`. So the shipped default really cannot
integrate.

TWO DEFECTS found, both by measurement rather than reading.

1. PR-001, BLOCKER. E-01 directs the driver to run the suite "in the SAME directory the turn worked in
   (the lane worktree when isolated)". MEASURED: `tests/test_run_viewer.py` gives **36 passed** in the
   primary checkout and **15 failed, 20 passed** in the lane worktree `.aw/worktrees/2c122z`. All 15
   failures are the `run_viewer` / state-resolution family, i.e. exactly the `dh0uno` signature (an
   inner `aw` resolves `.aw/state` relative to cwd, so a lane sees a different state tree). Gating
   integration on a suite run in the lane therefore makes `suite_result.passing` FALSE for reasons
   wholly unrelated to the plan under execution, so NOTHING would ever integrate. The plan would have
   replaced "integration never fires because `verify_disp` is None" with "integration never fires
   because the lane suite always fails" - the same symptom, a new cause. The plan even contains the
   contradiction internally: its own Required tests section says "validate in the PRIMARY checkout,
   never a scratch worktree (`dh0uno`)", which is the opposite of what E-01 tells the driver to do.
2. PR-002, MEDIUM. E-01 specifies `capture_command` with a `timeout` but does not fix a value, and the
   shipped default is **60.0 seconds** (`run_evidence.py:445`). The bare suite takes ~37s on this host,
   so the default leaves only ~23s of headroom; on a slower machine, under load, or as the suite grows,
   a PASSING suite would be recorded as exit 124 and refuse integration. Combined with E-02's
   (correct) fail-closed rule, an under-set timeout silently becomes "never integrate".

Both FIXED in place. The approach itself is sound and needed no replan: the fix for PR-001 is to name
the primary checkout as the suite's working directory, which the plan already argues for elsewhere.

Two things verified as GOOD, recorded because they materially de-risk implementation:

- E-02's fail-closed requirement is nearly free: `capture_command` already converts a timeout into
  exit **124** and any other exception into exit **127** (`run_evidence.py:469-475`) rather than
  raising, so "cannot run means fail" needs no new exception handling, just an honest reading of a
  nonzero exit.
- `capture_command` already supports `max_output_bytes` (`:446`, applied at `:482`), so a full suite
  log can be bounded without new machinery.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness / D. Anti-regression | MEASURED: `python3 -m pytest tests/test_run_viewer.py` gives `36 passed` in the primary checkout and `15 failed, 20 passed` in `.aw/worktrees/2c122z`; all 15 are the `run_viewer`/state-resolution family (`test_discover_run_dirs`, `test_load_run_summary_state_json`, `test_run_viewer_cli_*`), the `dh0uno` signature. Backlog `dh0uno` states the cause: an inner `aw` resolves `.aw/state` relative to cwd, so a lane resolves a different state tree. | E-01 tells the driver to run the suite in the LANE WORKTREE when isolated. In a lane, 15 tests fail for reasons unrelated to the executing plan, so `suite_result.passing` would be permanently False and NOTHING would ever integrate. The plan would trade one unreachable gate for another: "verify_disp is None" becomes "the lane suite always fails". The plan already contradicts itself on this point, since its Required tests section correctly says to validate in the PRIMARY checkout, never a scratch worktree, citing `dh0uno`. | C:Low; U:Low; S:Low; F:High; Overall:Low (the fix is naming the working directory, and the plan already argues for the primary checkout elsewhere) | FIXED | E-01 now REQUIRES the suite to run in the PRIMARY checkout (`repo`), never the lane, with the measured 36-vs-15 evidence and the `dh0uno` citation stated inline so an executor cannot "helpfully" switch it to the lane. Added the honest limit this implies: the suite then validates the MERGED-OR-MAIN tree rather than the lane's uncommitted state, so it proves the tree is green, not that the lane in isolation is. Added as F-10. V-01 now requires the working directory to be pasted as evidence. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing | `run_evidence.py:445` (`timeout: float = 60.0`); measured bare suite runtime ~37s on this host at HEAD `fbc8b32d` | E-01 passes a `timeout` to `capture_command` but fixes no value, and the shipped default is 60s against a ~37s suite. That is ~23s of headroom, which a slower host, background load, or ordinary suite growth would consume. Because E-02 (correctly) treats a timeout as a FAILURE, an under-set timeout silently degrades to "never integrate", reproducing the very class of bug this plan exists to fix. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now requires an EXPLICIT generous timeout (>= 900s, roughly 24x the measured runtime) rather than inheriting the 60s default, with the measurement and the reasoning recorded. E-02 now requires the timeout value and the measured runtime to be stated together so the headroom is visible, and V-02 requires both to be pasted. Added as F-11. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the driver-run suite execute in the lane worktree (where the work is) or the primary checkout (where the suite actually passes)? | PRIMARY CHECKOUT, with the honest limit recorded that it validates the merged-or-main tree rather than the lane in isolation. | (a) Run in the lane, as originally written. Rejected by measurement: 15 unrelated failures make the gate permanently closed. (b) Run in the lane but exclude the failing tests. Rejected: it hides a known bug behind a test filter, and the excluded set would silently rot as `dh0uno`'s blast radius changes. (c) Block this plan on fixing `dh0uno` first. Rejected as disproportionate: `dh0uno` is a graduated release blocker with its own fix already written on lane `7p9n2v`, and gating a small correctness fix on an unmerged 16-commit stack would strand this one indefinitely. | Measured 36 vs 15 across the two checkouts; backlog `dh0uno` root-cause statement; this plan's own Required tests section already mandating the primary checkout | yes |
| D-2 | Is a self-review a legitimate substitute for an independent review of a plan I authored? | NO, and it is disclosed as such in the Round 1 prose rather than presented as independent. Performed anyway, by attacking unmeasured assumptions rather than re-reading my own reasoning. | Skipping the review and implementing directly (the maintainer's stated preference was to implement in-session). Rejected because skipping review is precisely the failure that created checklist item 1, and the pass found a BLOCKER that would have made the implementation useless. | plan-review workflow memory kernel item 2 (verify claims from repository evidence); the PR-001 measurement is the concrete justification | yes |
