- Id: sovauj
- Status: open
- Set: setidxtype
- Priority: low
- Work-Kind: bug
- Summary: check.setid-collision reports a false cross-type collision when a walkthrough declares the Set of a plan still in pending/

## Workflow history
- 2026-09-17 created (aw backlog): check.setid-collision reports a false cross-type collision when a walkthrough declares the Set of a plan still in pending/

MEASURED 2026-09-18 at HEAD 36129255 while executing integpath child 05 (3v7wo6).

A walkthrough that declares '- Set: integpath' alongside its subject plan is reported as
check.setid-collision (severity error, invariant I-09): 'setid integpath conflicts with
.aw/records/plans/pending/20260907-integpath-05-3v7wo6-...ipd.md (different type: ...)'.

The rule in check_engine.py:894-916 treats a setid as owned by exactly ONE record type. But a Set is
a cross-type grouping in practice: the repository's own convention has walkthroughs, plans and specs
participating in the same Set, and several existing walkthroughs DO carry a '- Set:' line
(20260831-locksafe-01-5gdzyz, and the five 20260917 *closure walkthroughs).

WHY THOSE DO NOT FIRE, which is what makes this a latent trap rather than a consistent rule:
_iter_type_files (check_engine.py:522) skips retired files, and a plan in executed/ is retired. So a
walkthrough declaring its Set is CLEAN once the plan is filed to executed/ and DIRTY while the plan
is still in pending/. The verdict therefore depends on the subject plan's lifecycle position rather
than on anything about the walkthrough, and a walkthrough written before its plan finalizes (which is
the normal order, since the walkthrough is often the plan's own deliverable) trips it.

Workaround used: omit '- Set:' from the walkthrough and let the filename's setid slot plus
'Target-Id:' carry the grouping. That is lossy, because the frontmatter field is what a reader and a
tool see first.

Candidate fix: either exempt walkthrough-vs-plan from the different-type arm (a walkthrough is BY
DEFINITION about another type's artifact), or evaluate the rule against non-retired AND retired
plans so the verdict stops depending on lifecycle position. Do not fix by removing the rule; the
same-setid-different-descriptive arm is still worth keeping.
