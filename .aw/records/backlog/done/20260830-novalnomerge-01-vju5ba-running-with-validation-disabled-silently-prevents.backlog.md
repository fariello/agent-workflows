- Id: vju5ba
- Status: done
- Blocks-Release: next
- Set: novalnomerge
- Priority: high
- Work-Kind: bug
- Summary: Running with validation disabled silently prevents self-finalize, so every plan lands on an unmerged lane and integration becomes manual

## Workflow history
- 2026-09-01 done (aw set): Design shipped: plan evgi9n is executed (From-Backlog: vju5ba). Verified on main: the shared integration_is_earned predicate exists (5 hits), so a validation-off run reaches the integration gate instead of stranding every plan on a lane.
- 2026-08-31 graduated (aw set): Graduated to plan novalnomerge-01 (evgi9n), carrying From-Backlog: vju5ba and inheriting Blocks-Release: next. Root cause confirmed a BUG not a trade-off: --validate defaults False (oc_runipd.py:6000) while --no-self-finalize defaults True (:6007), so the shipped default has self-finalize on and unreachable, because verify_disp is only ever assigned inside the validate-guarded block (:4886-4963). Q1 answered by maintainer ruling: the verifier added only nits at ~33% cost on this model, so integration must not require it; the trust signal becomes a DRIVER-RUN suite (exit 0, zero failures) rather than the agent's decorative self-reported tests field, which is declared at :3676 and read by no code. Q2 (warn loudly) rejected as the primary fix: warning that the default is broken documents the bug. Q3 adopted as E-05. Q4 and the per-model default deferred to runprofile-01 (f2mrsw), which owns the profile schema.
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
