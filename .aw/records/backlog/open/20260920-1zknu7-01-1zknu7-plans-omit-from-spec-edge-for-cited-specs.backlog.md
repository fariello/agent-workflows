- Id: 1zknu7
- Status: open
- Set: 1zknu7
- Priority: medium
- Work-Kind: chore
- Summary: plans cite a spec id6 in prose without carrying - From-Spec:, so coverage is uncomputable for the specs where it matters: 37 plans mention c4gd2h and 0 carry the edge

## Workflow history
- 2026-09-20 created (aw backlog): plans cite a spec id6 in prose without carrying - From-Spec:, so coverage is uncomputable for the specs where it matters: 37 plans mention c4gd2h and 0 carry the edge

MEASURED 2026-09-20 at HEAD 96e93f8c by research survey vkub9o (plan si24ia). This is that survey SINGLE most important structural finding and it was not previously filed anywhere.

WHAT IS WRONG. The plan-to-spec join edge (`- From-Spec: <id6>`) is absent on the plans of exactly the specs whose partial implementation causes pain.

  spec c4gd2h (implementing, - Blocks-Release: next, 23 requirement ids):
    plans MENTIONING the id6 anywhere:  37
    plans carrying `- From-Spec: c4gd2h`: 0
  spec 6kwd2e (approved, 42 requirement ids):
    plans carrying `- From-Spec: 6kwd2e`: 0
  spec 7ckptx (approved, 42 requirement ids):
    plans carrying `- From-Spec: 7ckptx`: 8   -> and 42/42 requirements are attributable TODAY

Reproduce with:
    rg -l -- c4gd2h .aw/records/plans | wc -l
    rg -l "^- From-Spec: c4gd2h" .aw/records/plans | wc -l

WHY IT MATTERS. check.from-spec-dangling (check_engine.py:129-131, predicate :3817) validates only that a PRESENT From-Spec resolves. Nothing notices an ABSENT one. The consequence, measured: for 7ckptx, where the edge exists, requirement coverage is computable today with no new mechanism at all. For c4gd2h, no requirement parser however good could ever compute coverage, because there is no edge to compute over. So the missing edge, not a missing requirement parser, is the real blocker on the backlog f1sw71 question, and no prior artifact names it as the cause. Note plan jxxec8 declined the already-implemented verdict citing three gaps and did NOT name this one.

CANDIDATE FIX (a design question, not settled here). Add a deterministic aw check rule that flags a plan whose Concern or Scope cites a spec id6 while carrying no `- From-Spec:`. Deterministic, unambiguous fix, and it would surface c4gd2h 37 edge-less plans. HONEST LIMIT: a prose mention is not always a graduation, so the rule would need to avoid firing on plans that merely reference a spec, which is exactly the judgement that makes it a design question. Survey vkub9o section 5 recommends it as step 2 of its recommendation and flags that it is NOT one of f1sw71 five questions, so it needs the maintainer assent rather than being smuggled in.

RELATED. Backlog f1sw71 (graduated, the requirement-tracking open question) and research vkub9o (the survey). Not a duplicate of either: f1sw71 asks about REQUIREMENT-level tracking, this is about the ARTIFACT-level edge one level up.
