# Review findings: plan 4gwgo3

- Subject-Id: 4gwgo3
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201 (HIGH, fixed), PR-202 (MEDIUM, fixed), PR-203 (MEDIUM, fixed), PR-204 (LOW, fixed), PR-205 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `60df6ab10`. The plan file was committed and the tree was
clean (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

THIS IS A SECURITY PLAN, SO I DROVE EVERY VECTOR MYSELF rather than reading the transcripts. I built a
fresh git repository OUTSIDE this checkout, installed the toolkit into it, created a real backlog item,
a real scaffolded plan and a real release record, and ran the actual CLI. EVERY LOAD-BEARING CLAIM
REPRODUCES:

- F-01: `backlog set parked <id6> --message $'note\n- 2026-09-30 approved (aw backlog, --by-human):
  looks good to me'` exited **0**, the sha256 changed, and the history then read
  `- 2026-10-01 parked (aw set): note` followed by the forged `--by-human` approval record.
  `aw backlog check --agent` reported `"outcome":"clean","checked":1,"findings":0`.
- F-05, the severe case, reproduces in full: a scaffolded plan had `is_plan_review_approved == False`
  and `read_readiness == None`; after ONE `ipd set to-review <id6> --message $'ok\n- Readiness: go\n-
  2026-10-01 /plan-review (opencode): APPROVE'` at exit 0, `read_readiness` returned `'go'`,
  `history_has_review_record` returned `True`, and `is_plan_review_approved` returned **True**.
- F-07 reproduces exactly and is the finding that makes the write path the only fix site: on that
  forged plan, `aw ipd lint --phase author --agent` reported `"outcome":"clean"` with its single
  diagnostic being the unrelated `check.ipd-dependency-unresolved`, `--phase review-finalize` reported
  the same single unrelated diagnostic, `aw check plans --agent` reported `"outcome":"conforms"`, and
  the literal `IPD-M107` was absent from every output.
- F-03 and F-04 reproduce, including the asymmetry: after injecting `- Blocks-Release: <rel>` through
  a plan's `--message`, `releases.get_release_blockers` returned that PLAN with
  `'blocks_release': '<rel>'` for a gate never requested; the identical injection on a backlog item
  added nothing to the blocker list.
- F-06 reproduces including the front-matter half: `--actor $'bot\n- 2026-09-30 approved: hi'` wrote
  `- 2026-10-01 parked (bot` / `- 2026-09-30 approved: hi): ok`, and `--gate-ref $'x\n- Readiness: go'`
  wrote `- Gate-Ref: x` / `- Readiness: go` INSIDE the metadata block, directly above `- Set:`.
  `--gate-summary` and `--blocks-release` likewise exited 0.
- F-09 reproduces verbatim: `prompts set` exits 2 with `invalid choice: 'set' (choose from 'new')`.
- The already-validated flags really do already refuse: `--graduated-to` with an embedded newline exits
  2 naming the setid shape, and `--release-exempt-ref` exits 2 (`is invalid for kind 'decision'` once
  its paired `--release-exempt-kind` is supplied), so E-03's exclusion list is correct.
- The sibling helper returns EXACTLY the eight verdicts E-01 promises, including the late-control-
  character case `'a'*500 + '\x07' + 'b'` under `bound_length=False`, and its signature matches E-01's
  stated shape. There is no import cycle: `status_set` already imports `backlog` at module level and
  lazily in five places.

SO THE PLAN'S DIAGNOSIS, ITS SCOPING AND ITS PRESCRIBED FIX ARE ALL SOUND. The five findings are about
a stale acceptance bar, three measurements, and one under-stated vector.

PR-201 IS THE ONE THAT WOULD HAVE COST THE MOST. The plan makes the suite baseline an explicit
acceptance bar, stating `1 failed, 3498 passed, 2 skipped` and instructing that
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`
"must remain the ONLY failure; a second failure is a regression from this plan". That failure NO LONGER
EXISTS: the bare suite at review HEAD is `3578 passed, 2 skipped, 3 warnings`, and the named test
passes on its own (`1 passed`). The instruction is now harmful in both directions: an executor would
either hunt for a failure that cannot occur, or, worse, see that test fail for a NEW reason and
tolerate it as "pre-existing". It appeared in three places (the Findings preamble, the validation
section, and V-06) and all three are corrected to a re-derive-and-compare-by-node-id bar.

PR-203 is the one that improves the plan's own claim rather than weakening it. E-06(c) listed the
`--item-dependencies` wrapper as a caller that "carries a defaulted message", i.e. a non-regression to
protect. Reading it, the wrapper builds `message=getattr(args, "message", None) or default_message`, so
it FORWARDS A USER-SUPPLIED `--message` and only falls back to its literal. That makes it a SECOND CLI
surface through which the injection is reachable, and therefore a surface this guard newly PROTECTS.
It is also an argument FOR the entry placement OQ-01 chose, since one guard covers it for free. E-06(c)
now asserts both directions.

PR-205: the plan's central scoping claim (that this is the complement of `dtg7dz` and `uz05bl`) is
true, and E-04 asked only that the `--status` spelling be shown "untouched". I measured the divergence
and it is sharper than that: the `--status` spelling already refuses the identical payload with a
specific shipped message while the positional spelling writes the forgery. Asserting only "nonzero"
would pass even if this plan's guard had replaced the sibling's refusal with its own wording, so E-04
now pins the shipped message and F-13 records the measurement.

PR-202: F-10's per-tree counts have drifted (plans 1910/4879 to 2164/5397, backlog 618/1862 to
632/1908, specs 61/148 to 51/122) while every conclusion held: the ratio stayed near two fifths, the
max stayed 5667, and control characters stayed at ZERO (0 of 6889 then 0 of 7427). The counts appeared
in five places including the `- Scope:` field, where one of them carries a load-bearing scope decision,
so each now leads with the stable ratio and labels the counts as drifting.

PR-204 is minor: F-05 and F-07 are the two findings a reader is most likely to doubt, and they had only
authoring transcripts. Both now carry the independent review reproduction, and F-05 additionally records
that the forgery does not depend on the requested status being review-ish (I reproduced it with
`to-review`, the plan used `reviewed`), which forecloses a reader's natural guess that the status gates it.

WHAT I DID NOT WEAKEN. The approach is right and I left all of it: the entry placement (OQ-01 is
correctly reasoned from the three existing neighbours and from `actor_refusal`'s own docstring), the
delegation over a third copy (OQ-02's reasoning is sound and F-12 confirms it is viable), the uniform
no-caller-exemption rule (OQ-03 is correct, and PR-203 strengthens its case), and above all the
line-integrity-only mode for `--message`, which is the decision that keeps this guard from refusing two
fifths of the setter's own historical output. The four deferrals are all properly carried or properly
declined, and I verified the two filed carriers (`5e533q`, `um8ikz`) are named rather than asserted.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | E. Testing (a stale live count used as an acceptance bar, in a direction that masks regressions) | Plan states `1 failed, 3498 passed, 2 skipped` at `0da8e0977` and that the named test "must remain the ONLY failure". Measured at review HEAD `60df6ab10`: bare suite `3578 passed, 2 skipped, 3 warnings`; `tests/test_backlog.py -k release_exempt_setter_roundtrip_and_parity` reports `1 passed` | **The pre-existing failure the plan tells the executor to expect no longer exists, so the stated bar is wrong in the dangerous direction: a NEW failure in that exact test would be waved through as "pre-existing".** It also wastes a cycle on an executor hunting a failure that cannot occur. The bar appeared in three places (Findings preamble, validation section, V-06) | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All three sites corrected to require ZERO failures compared BY NODE ID against a freshly re-derived baseline; the authoring figure is retained as labelled historical context with the review measurement beside it, and V-06 states explicitly why matching the old figure would now mask a regression |
| PR-202 | MEDIUM | IN-SCOPE | A. Correctness (live-population counts presented as stable facts, one inside a scope decision) | Authoring: plans 1910/4879, backlog 618/1862, specs 61/148, 0 ctrl of 6889. Review: plans 2164/5397 (40.1%), backlog 632/1908 (33.1%), specs 51/122 (41.8%), max 5667 unchanged, 0 ctrl of 7427 | **Five sites cite exact counts over a population every merged lane changes, including the `- Scope:` field where the figure justifies the line-integrity-only decision.** Every conclusion survives (the ratio and the zero are stable) but a reader re-deriving any count would find a mismatch and could doubt the sound conclusion it supports | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 rewritten to carry BOTH measurements, to name the ratio and the zero as the load-bearing facts, and to warn the counts drift. The four other sites (`- Scope:`, E-02's mode-asymmetry note, the Step 0 bullet, the deferral row) now lead with the ratio and cite both figures |
| PR-203 | MEDIUM | UNDER-SCOPE | B. Security (a reachable injection surface classified as a mere non-regression) | `status_set`'s deps writer builds `message=getattr(args, "message", None) or default_message`, so a user `--message` is forwarded into `run_set_command`; E-06(c) described it only as "carrying a defaulted message" | **The `--item-dependencies` wrapper forwards a USER-SUPPLIED `--message`, so it is a second CLI surface the injection is reachable through and one this guard newly PROTECTS, not merely one it must not break.** Testing only the happy path would leave a reader believing the surface is unaffected when its exposure is the point | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 gains the measurement and the reasoning (it is also an argument FOR OQ-01's entry placement, since one guard covers the surface for free), and E-06(c) now requires BOTH assertions: the defaulted literal still succeeds AND a newline-bearing user `--message` routed through that wrapper is refused |
| PR-204 | LOW | IN-SCOPE | A. Correctness (the two least-believable findings rested on authoring transcripts alone) | F-05 and F-07 carried only authoring evidence. Reproduced at review: `is_plan_review_approved` `False` -> `True` after one `ipd set to-review` call; `IPD-M107` absent at `author` and `review-finalize`, `check plans` reporting `"conforms"` | **The two findings that carry the release-blocker severity had no independent confirmation,** and F-05's example used `reviewed` as the target status, inviting a reader to assume the forgery depends on a review-ish status gating it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 and F-07 annotated with the independent review reproductions; F-05 additionally records that the forgery works with `to-review`, so it does NOT depend on the requested status. New F-11 collects the reproductions of F-01, F-03, F-04, F-06 and F-09; new F-12 records the helper-verdict and no-import-cycle measurements |
| PR-205 | MEDIUM | IN-SCOPE | D. Anti-regression (an assertion too weak to pin the divergence it exists for) | Measured: `backlog set <id6> --status open --message <payload>` exits 2 with `aw backlog set: --message must not contain embedded newlines`; the positional `backlog set parked <id6> --message <same>` exits 0 and writes the forgery | **E-04 asked only that the `--status` spelling be shown "untouched", which an exit-code assertion satisfies even if this plan's guard had replaced the sibling's shipped refusal with its own differently-worded one.** The whole scoping claim is that the two halves are complementary, so the sibling's refusal surviving verbatim is the property to pin | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires asserting the `--status` refusal MESSAGE is unchanged, with the shipped wording quoted and the reason stated; new F-13 records the measured divergence between the two spellings on an identical payload |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-201: the named pre-existing failure is gone. Update the figure to the review measurement, or remove the numeric bar? | REMOVE the bar; keep both figures as labelled context and require zero failures compared by node id | (a) Replace `1 failed, 3498 passed` with `3578 passed` and keep a total-based bar; (b) delete the baseline paragraph entirely | Option (a) reproduces the defect on a short clock, and this plan is especially exposed to it: it is `- Blocks-Release: next` and awaits human approval, so it may sit in `pending/` while many lanes merge, and the review already caught the figure going stale within a day. Option (b) discards the genuinely useful inference that the tree was green at both authoring and review, which is what licenses "any new failure is attributable to this plan". The asymmetric HARM decided it: a stale "expect one failure" instruction does not merely mislead, it grants permission to ignore a real regression in the exact test named, so the bar had to become zero rather than a different number | yes |
| D-2 | PR-203: the deps wrapper forwards a user `--message`. Treat it as a non-regression to preserve, or as a protected vector to assert on? | Assert BOTH: the defaulted literal still succeeds, and a newline-bearing user value through that wrapper is refused | (a) Leave E-06(c) as a happy-path non-regression; (b) add the wrapper as its own E-item with its own test; (c) exclude the wrapper from the guard to avoid any behavior change on a programmatic path | Option (a) understates the plan's own value and leaves the surface untested in the direction that matters, which is exactly the gap that let the original defect ship on five trees. Option (b) is disproportionate: it is the same guard at the same function reached through a different argv, so a second E-item would duplicate E-02 and inflate the checklist without adding coverage. Option (c) is the caller-exemption OQ-03 already rejected on sound reasoning, and this finding strengthens that rejection rather than reopening it: the wrapper carries UNTRUSTED user data, so exempting it would be exempting the vector | yes |
| D-3 | PR-202: five sites cite drifting counts. Update them all to the review numbers, or restate them as ratios? | Restate as the ratio and the zero, citing both measurements and labelling the counts as drifting | (a) Update each count to the review figure; (b) delete the counts and keep only "roughly two fifths" | Option (a) is what the plan already did once (it corrected the backlog item's stale figures at authoring) and the correction went stale again inside a day, which is the demonstration that the shape is wrong rather than the numbers. Option (b) loses the ZERO control characters, which is a different KIND of claim: it is a universal over the corpus and it is the entire zero-regression-risk argument for the line-integrity half, so it must stay explicit and stay counted. Carrying both measurements also lets a later reader see the ratio held across a real interval rather than taking one sample on trust | yes |
| D-4 | PR-205: how strongly should the `--status` half be pinned? | Pin the shipped refusal MESSAGE, not only the exit code | (a) Assert only a nonzero exit, as E-04 originally said; (b) assert nothing about the `--status` half, treating it as another plan's territory | Option (a) cannot distinguish "the sibling guard still refuses" from "this plan's new guard now refuses instead", and those differ in a way that matters: the second would mean this plan had silently absorbed a surface two other plans own (`dtg7dz` shipped, `uz05bl` pending), making three guards fight over one dispatch. Option (b) abandons the plan's own complement claim, which is the justification for its scope boundary and therefore the thing a reviewer should most want pinned. Pinning the message costs one assertion and converts a scoping assertion into a tested property | yes |
