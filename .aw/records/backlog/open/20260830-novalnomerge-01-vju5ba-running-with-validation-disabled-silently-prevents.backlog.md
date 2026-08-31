- Id: vju5ba
- Status: open
- Blocks-Release: next
- Set: novalnomerge
- Priority: high
- Work-Kind: bug
- Summary: Running with validation disabled silently prevents self-finalize, so every plan lands on an unmerged lane and integration becomes manual

## Workflow history
- 2026-08-30 created (aw backlog): Running with validation disabled silently prevents self-finalize, so every plan lands on an unmerged lane and integration becomes manual

OBSERVED 2026-08-30 across five overnight runs and then again on four resumed runs. This single
setting is the root cause of an entire night of manual integration.

THE MECHANISM. The driver's self-finalize gate requires BOTH a successful disposition AND
`verify_disp == "verified"`:

    if self_finalize and not is_review
       and disposition in ("executed", "substantially-complete")
       and verify_disp == "verified":

`verify_disp` is only ever set by the verifier turn, which runs only when validation is enabled. With
`--no-validate` (or the default `validate: false` in the run options) NO verifier runs, so
`verify_disp` stays `None`, the gate NEVER fires, and every item ends `substantially-complete` with
its lane PRESERVED rather than integrated.

MEASURED CONSEQUENCE. The overnight batch of five runs spent about $528 and produced 21 plans whose
work self-finalized INSIDE their lanes and never reached main. Every one showed
`Expected executed/ | Actual pending/` in the run report's discrepancy table. Landing them took a
full session of hand-merging: 24 lane merges, several with real conflicts, plus 4 backlog defects
discovered along the way. Nothing was lost, but nothing was integrated either.

WHY THIS IS WORTH FIXING RATHER THAN DOCUMENTING. The maintainer disabled validation for a defensible
reason: it added roughly 33 percent to cost and, with a stronger model, caught little. That is a
legitimate trade. What is NOT legitimate is that the trade SILENTLY also disables integration. The
operator asked for "spend less on verification" and unknowingly also got "nothing merges". Those are
unrelated concerns wired to one flag.

WHAT TO SOLVE FOR.

1. Should integration depend on VERIFICATION at all, or on something weaker? The gate exists so an
   unverified turn cannot mark itself executed, which is right. But "did the tests pass" and "did an
   independent verifier session bless it" are different bars. A cheap deterministic check (suite
   green, lint conforming, V-items evidenced) might be enough to earn integration without a full
   verifier turn.
2. If the answer is no, should the runner REFUSE OR WARN LOUDLY when validation is off? Right now it
   proceeds silently and the operator discovers the consequence hours later in a discrepancy table. A
   startup notice saying "validation is off, so no item will self-finalize and every lane will need
   manual integration" would have changed the decision.
3. Should `--no-validate` imply a DIFFERENT terminal state than `substantially-complete`? That status
   currently conflates "verifier said no" with "no verifier ran", which is the same intent-versus-
   breakage conflation spec `c4gd2h` R21 forbids elsewhere.
4. Is there a middle setting? Verify only the LAST item of a Set, or only items touching declared
   high-risk paths, would restore integration for most work at a fraction of the cost.

RELATED. Backlog `gjadwm` (the executed-transition gate cannot see a consumed finalize journal) is
what makes the resulting MANUAL merges require `--no-verify`, so these two defects compound: validation
off forces hand-merging, and hand-merging trips a gate that then has to be bypassed. Backlog
`resumedupe` also compounds it, since more preserved lanes means more resumes.
