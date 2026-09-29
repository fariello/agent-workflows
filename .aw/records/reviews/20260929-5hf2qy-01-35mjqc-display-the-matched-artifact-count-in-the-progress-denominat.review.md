# Review findings: plan 35mjqc

- Subject-Id: 35mjqc
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `67e532f6` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after. No pre-review snapshot was owed: the plan was committed and unmodified. `aw check` reports no
finding against this plan, and `aw check release-gates` conforms, so the `- Blocks-Release: next`
inherited from backlog `5hf2qy` (a `bug`, per the every-live-bug-gates-the-release rule) is well
formed and resolves to the single planned release. `agent_workflows/render_stream.py` was prototyped
against TWICE and restored both times; `git diff --stat` on it is empty and the working tree holds
only this plan's own edit.

THE DIAGNOSIS, THE REJECTED ALTERNATIVES, AND THE CHOSEN FIX WERE ALL REPRODUCED, the last one
prototyped end to end, because a plan that resolves an open design question from measurement is only
as good as the measurement it rests on.

F-01 reproduces exactly: rendering the real `render_run_summary_table` over eight `reviewed`
zero-attempt items yields `Progress: 0/1  [          ]   0% (8 reviewed)` and
`Total (0/1 items run)` with EIGHT per-artifact rows between them. F-03's widened blast radius
reproduces too, which matters because the backlog item never mentioned it: the all-five-pre-executed
shape renders `0/1` above five rows with `Outcome: COMPLETED`, and the mixed shape renders `0/1` above
three. Every one of the nine BEFORE rows matched the plan's matrix, and `dispatchable_work_total`
returned 1/1/6/1/0 on E-01's five named shapes with a RAW pre-guard count of 0/0/6/0/0, so E-01's five
expected values are arithmetically consistent with the rule it states.

F-04 reproduces AND IS STRONGER THAN THE PLAN CLAIMS, which is the most useful thing this review
found beyond the corrections below. Deleting the `or 1` does relabel the eight-`reviewed` shape from
`NO WORK PERFORMED` to `QUEUED`, but it relabels FIVE of the nine shapes, every one whose raw
dispatchable count is 0, including the legitimately-`COMPLETED` all-pre-executed run. It also FAILS 8
of the 21 tests in the two suites this plan pledges not to disturb, so the naive fix would not have
shipped silently. Both facts strengthen the plan's central choice and are now recorded, the second so
an executor who tries the deletion recognises those failures as the predicted regression rather than
as unrelated breakage.

The CHOSEN fix was prototyped rather than reasoned about. A separate `progress_display_total`
accessor consumed only by the progress bar and the totals label produced the plan's F-07 AFTER matrix
row for row (`0/8`, `0/1`, `0/2`, `0/5`, `6/6`, `3/3`, `0/3`, `0/0`, `0/1`) with NO outcome word
changed in any shape; a unified diff of the eight-`reviewed` render before and after touched exactly
two lines, the progress line and the totals row, confirming V-02's scope claim; the two pinned suites
stayed at `21 passed` UNMODIFIED, confirming F-05; and a BARE full suite reported `3246 passed, 2
skipped, 3 warnings`. F-05's byte-pinned string reproduces verbatim in
`tests/test_zero_dispatch_outcome.py`, and because the single-`reviewed` shape's denominator is 1 both
before and after, that pin is genuinely untouched. F-06's pre-banner mutation went raw 0 -> 1 in
source order. F-08 reproduces verbatim (`total: 8 matched, 0 acted on, 8 not acted on`). F-09
reproduces: `rg 'Progress:' .aw/records/specs/` returns zero hits, so no spec pins the fraction's
format.

This is a careful, well-evidenced, correctly-scoped plan and review found no fault in its design.
What it found is one miscounted call-site set that E-01 builds a required docstring on, and three
smaller precision issues.

**THE SHARED PREDICATE HAS THREE CONSUMERS SPELLED TWO WAYS, NOT "BOTH HOSTS" (PR-301, HIGH).** The
plan states in its `- Scope:`, its conventions section, and F-06 that `dispatchable_work_total` is
consumed by "both hosts" binding `total_items = dispatchable_work_total(queue) or 1`, and E-01
REQUIRES the new accessor's docstring to explain the separation on that basis. Measured, there are
three call sites: `runner_shared.run_ipd` binds it BARE (`total = dispatchable_work_total(state["queue"])`)
for the `IPD nn/NN` banner, while `oc_runipd` and `agy_runipd` each add their own `or 1` for the live
4-line statusline. Two consequences. First, the hosts' `or 1` does NOT guard the banner; the banner
relies on the accessor's own internal fallback, and it lives in a module the plan never names.
Second, a docstring written from the plan's description would assert something false about the code it
sits in, in the one artifact this plan produces to prevent a future reader "simplifying" the two
accessors back together. F-06's unreachability argument is unaffected and holds for all three sites,
since all three are reached only for an item already mutated to `running` with an appended attempt.
Fixed in `- Scope:`, the conventions section, F-06, E-01 and the deferral row.

**V-01 COULD NOT FALSIFY "NO LIVE DISPLAY MOVED" (PR-302, MEDIUM).** V-01 requires a transcript of
both accessors' return values, which proves the new accessor's arithmetic and the old one's behavior
but says nothing about whether a CALL SITE changed. That gap has a specific trigger: PR-301 exposes
that the two host `or 1` bindings are now provably redundant, which is exactly the kind of thing an
executor tidies while in the file, and doing so would alter live-run output this plan disclaims. V-01
now additionally requires a `rg dispatchable_work_total agent_workflows/*.py` census at the executing
HEAD whose only difference from today is the ADDITION of the new definition.

**TWO PRECISION SLIPS (PR-303 LOW, PR-304 LOW).** The plan writes "`b7oicl`/`4po0sc`" in F-04 and the
deferral section as though naming two plans; they are one plan (`- Set: b7oicl`, `- Id: 4po0sc`), and
a reader chasing two records would find one. And F-04's own evidence understated its scope (one shape
named, five measured), which mattered because F-04 is the finding that selects the entire design.

Every finding is FIXED. None was deferred, so no escalation to a `- Blocking: yes` question is owed.

BOTH OPEN QUESTIONS ARE CORRECTLY RESOLVED AND SURVIVE REVIEW. OQ-01 chose `0/8` over the two
alternatives on measured grounds that both reproduce: suppression breaks F-05's `lines[3]` byte pin
and its line indexing, and the true `0/0` regresses the outcome word (F-04, now measured five times
over). Its stated meaning for the fraction is honest about being dual, and confining that duality to
the summary renderer is what keeps the live banner on a single unit. OQ-02 correctly folds F-03's
all-already-executed shape into this plan, because it is the same expression in the same function
fixed by the same change, and pins it explicitly in E-03(b) precisely because the item never mentioned
it. Note both questions carry `- Owner: none`, which `aw ipd lint` accepts for a resolved question and
which is honest here (the plan author resolved them from its own measurement), though `- Owner:` naming
the resolving author would read better.

The plan's other choices were checked and are right: two files and one new accessor is minimal for the
defect; E-03's six shapes include the two byte-identity controls that prove the neighbouring fixes are
undisturbed; the deferral rows all carry well-argued `Carrier-Declined` reasons that correctly
distinguish a prohibition-on-this-plan from deferred work; the `- Under-scope:` note honestly admits
the `or 1` remains visible in the old accessor rather than hiding it; E-03 asserts on rendered text
rather than introspecting source, per GUIDING_PRINCIPLES 16; and the gate carries the honesty rule,
the path-scoped commit obligation, the shared-checkout re-verification warning, and a tooled
lifecycle transition.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | high | IN-SCOPE | C. Architecture and operability | `rg dispatchable_work_total agent_workflows/*.py` -> `runner_shared.run_ipd` `total = dispatchable_work_total(state["queue"])` (bare), `oc_runipd` and `agy_runipd` `total_items = dispatchable_work_total(queue) or 1` | The plan says "both hosts" consume the predicate with `or 1` and makes that the basis of E-01's REQUIRED docstring. There are three consumers spelled two ways, and the banner's guard is the accessor's own internal fallback in a module the plan never names, so the mandated docstring would assert something false. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | `- Scope:`, the conventions section, F-06, E-01 and the deferral row all corrected to name three sites and both spellings; E-01 now requires the docstring to enumerate all three accurately or not enumerate at all. |
| PR-302 | medium | UNDER-SCOPE | E. Testing and verification | V-01 as authored (return-value transcript only); PR-301 exposing the host `or 1` as provably redundant | V-01 proves the accessors' values but cannot detect a changed CALL SITE, and PR-301 creates a concrete temptation to tidy the now-redundant host `or 1`, which would alter live-run output the plan disclaims. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | V-01 now requires a `rg dispatchable_work_total agent_workflows/*.py` census whose only delta is the new definition. |
| PR-303 | low | IN-SCOPE | Evidence accuracy | `.aw/records/plans/executed/20260928-b7oicl-01-4po0sc-...ipd.md` front matter `- Set: b7oicl`, `- Id: 4po0sc` | F-04 and the deferral section write "`b7oicl`/`4po0sc`" as if naming two plans; it is one plan's setid and id6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Both references now name one plan and say so explicitly. |
| PR-304 | low | IN-SCOPE | Evidence accuracy | re-prototyped `or 1` deletion over all nine shapes; `8 failed, 13 passed` on the two pinned suites | F-04 named one regressed shape where five regress, and did not record that the existing suite catches the naive fix. Both matter because F-04 selects the whole design. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-04 restated with five shapes and the suite result; a full re-prototyped matrix added under Measured evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan resolves a design question the backlog item left open, by measurement. Accept the reasoning, or re-derive it including prototyping the chosen fix? | Re-derive everything, and prototype BOTH the rejected `or 1` deletion and the chosen separate-accessor fix, each with the two pinned suites and a full bare suite. | (a) Accept the reasoning: rejected because OQ-01 selects among three options on measured grounds, so an unreproduced measurement would leave the design choice unaudited; the plan is also `Blocks-Release: next`, which raises the cost of a wrong design. (b) Reproduce only the defect: rejected because the defect was never in doubt; the contested part is that the obvious fix regresses a neighbouring shipped fix, which is only checkable by applying it. | Nine-shape BEFORE matrix matching row for row; `or 1` deletion flipping five outcome words and failing `8 of 21`; chosen fix matching F-07 row for row with `21 passed` on the pinned suites and `3246 passed, 2 skipped` bare; two-line unified diff of the eight-`reviewed` render. | yes |
| D-2 | The call-site miscount: raise it as a blocking question, or correct the plan in place? | Correct in place, in all five locations that carry the claim. | (a) Blocking question: rejected because the repository answers it mechanically (`rg` over `agent_workflows/*.py` enumerates the three sites and their spellings), so it is a fact, not a maintainer judgement. (b) Correct only F-06: rejected because E-01 MANDATES a docstring built on the claim, so leaving `- Scope:` and the conventions bullet uncorrected would let the false statement reach the shipped artifact through a different path. | The three call sites read at HEAD `67e532f6`; `runner_shared.run_ipd`'s bare binding sits in a module the plan's conventions bullet never names. | yes |
| D-3 | The two host `or 1` bindings are provably redundant once F-06 is accepted. Should this plan remove them? | No. Leave them, and add a V-01 census that catches their removal. | (a) Remove them as cleanup: rejected because they are outside `- Scope-Paths:`, they affect live-run output this plan explicitly disclaims, and F-06 establishes only that the fallback is never REACHED, not that removing a defensive guard is free. (b) File a carrier for their removal: rejected as recording a defect nobody has observed; the plan's own deferral row already argues this correctly for the accessor itself, and the same reasoning covers the redundant guards. | F-06's raw 0 -> 1 mutation showing the fallback unreachable at all three sites; the plan's `- Scope-Paths:` naming only `render_stream.py` and the new test. | yes |
