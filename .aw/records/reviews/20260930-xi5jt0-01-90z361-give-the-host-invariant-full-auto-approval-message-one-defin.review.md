# Review findings: plan 90z361

- Subject-Id: 90z361
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e4474af7`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `clean` with zero findings after revision. The plan is `- Kind: child`,
so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S CENTRAL ARGUMENT IS SOUND AND I RE-RAN IT RATHER THAN TRUSTING IT. Every one of F-01 through
F-09 reproduces, and the plan's one substantive departure from its backlog item (refusing the item's
suggested `HostLabels` field) is correct for the reasons it gives:

- F-01 reproduces exactly. Both hosts assign `FULL_AUTO_APPROVAL_MESSAGE` as an independent literal;
  both assign `FULL_AUTO_ACTOR` as a `runner_shared.<OC|AGY>_HOST_LABELS.full_auto_actor` reference. The
  two message values are `==` True and `is` False with distinct `id()`s.
- F-02 reproduces. `inspect.signature(runner_shared.set_plan_approved).parameters["message"].default` is
  `inspect._empty`; each host's wrapper default IS that host's own constant; and both live call sites
  (`set_plan_approved_fn(repo, id6)` and `set_plan_approved(repo, item["id6"])`) pass two arguments.
- F-04 reproduces to the number and is the strongest finding in the plan. All 10 `HostLabels._fields`
  differ between the two descriptors, ZERO are equal, `_field_defaults` is `{}`, and
  `DEPENDENCY_BLOCK_RECOVERY_HINT` is measured host-VARYING, making it a disanalogy rather than the
  precedent plan `8eei5p` treats it as. So the item's proposed field would have made a host-INVARIANT
  value into a per-host parameter.
- F-07 and F-08 reproduce. 8 of the co-defined constants are already reference-style in both hosts; the
  shipped predicate is literally `if v_shared != v_oc and v_shared != v_agy`, so it permits a shared
  value equal to both and is structurally blind to `v_oc != v_agy`. The three-way intersection the
  shipped sweep actually covers is 8 names, all satisfying `shared == oc == agy`.
- F-09 reproduces to the exact eleven names.

THE DOMINANT FINDING IS A CROSS-PLAN COLLISION, and it is the kind that is invisible unless you read the
sibling plans' E-items rather than their titles. The plan's own F-11 claimed `b02ohu` and `76ic0k` mention
this surface "only in prose". Reading them refutes that: `b02ohu` declares
`tests/test_runner_shared.py` in `- Scope-Paths:`, is `- Status: approved`, and its E-05 REWRITES the very
helper this plan's E-03 told the executor to reuse, while its E-04 and E-06 each demand a pasted search
showing ZERO `ast.parse`/`ast.unparse`/`ast.walk` remain in that file. Its E-02 also edits
`test_set_plan_approved_durable_history_pin`, which this plan's E-04 proposed adding to. And `76ic0k`
(also `approved`) ships a guard that REFUSES a new AST read in a test module. So the authored E-03 would
have been reverted by one approved plan and refused by another, and nothing in this plan would have
noticed.

I RESOLVED THE HOW QUESTION BY DEMONSTRATION RATHER THAN BY DESCRIPTION, as the workflow requires for a
mechanism choice. The replacement `vars()` sweep was written and driven at review:

```
compared: 55
failures: NONE

baseline: GREEN
after mutating ONE host: ["FULL_AUTO_APPROVAL_MESSAGE: oc='drifted message' agy='auto-approved by --full-auto: review readiness cleared (not human approval)'"]
restored: GREEN
```

That failure text is exactly what E-03's `Expected outcome` demands (the constant plus both host values),
so the mechanism is proven to fire and proven to recover, not merely asserted to.

I ALSO MEASURED THE MECHANISM'S COSTS rather than substituting one unexamined mechanism for another.
`vars()` reaches 57 co-defined `isupper()` names where the AST walk reached 19, and 48 of the 57 are the
SAME OBJECT in both hosts (re-exports, where divergence is impossible), leaving nine real subjects. That
is the same widening `b02ohu` E-05 measured independently (39 common / 38 identity / 1 co-defined, over
the three-module intersection) and chose to accept, so the two plans' shapes agree. Separately,
`"_close_process_streams".isupper()` is False, so the sweep does NOT reach F-09's eleventh name; it needs
no coverage (both hosts bind the identical `runner_shutdown` object) but the plan's claim that E-03
"covers all eleven" was wrong and is now corrected to nine.

THREE SMALLER CORRECTIONS, each a measurement rather than a style preference.

E-01 told the executor to write a code comment stating the shared constant's value is "enforced by the
E-03 guard". That is false and it is the inversion the plan elsewhere gets right: after E-02 both hosts
follow the shared constant in lockstep, so E-03's host-vs-host check stays GREEN when the SHARED value
drifts. E-04 is the guard that catches it, which the plan's own V-04 already demands a demonstration of.
A comment asserting the wrong guard would mislead the next person to edit the value.

The suite baseline is stale and the tree is not green. The plan cites `3387 passed, 2 skipped`; measured
at review HEAD, bare `python3 -m pytest` reports `1 failed, 3414 passed, 2 skipped, 3 warnings in 82.54s`.
The single failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`,
comparing a history line stamped `2026-09-30` against one stamped `2026-10-01`: a date-rollover flake in
the backlog setter, touching no path this plan declares. Worth recording for two reasons. An executor
comparing against the authored number would see a count mismatch and could not tell whether it caused
it; and an executor told "the suite must be green" would be given an impossible bar by a defect that is
not theirs. V-04's bar is now re-derive-before-and-after and attribute any failure present in both runs.

The `_ID_RE`/`_STATUS_RE` deferral reason is weaker than stated, which does not change the deferral but
does change what it rests on. Both the plan and its carrier item offer "they are compiled patterns" as a
reason these need separate judgement, implying comparison is problematic. `re.Pattern` implements VALUE
equality: two independently compiled patterns with the same pattern and flags compare equal while being
distinct objects, and differing text or flags compare unequal. Verified on 3.9.25, 3.11.15, 3.12.3 and
3.14.6, spanning the whole `requires-python = ">=3.9"` matrix that CI tests. So E-03's sweep compares them
soundly; the real reason to defer is deciding where a compiled pattern should live.

ONE THING I CHECKED AND DID NOT FLAG. The plan reintroduces a constant NAME that `gjni4c` deliberately
deleted, which looks alarming and is not: the deleted constant held a THIRD value matching neither host,
and the hazard was that divergent value rather than the sharing. The plan already carries that reasoning,
already requires it in the code comment, and E-04 pins the value by literal with a negative assertion on
the deleted string. That is the right treatment and I strengthened only where it cited the wrong guard.

ALSO REPAIRED: the plan's `## Workflow history` had its `draft` and `to-review` records in oldest-first
order, which inverts the documented newest-first convention. Harmless while unnoticed, it became a real
`aw check` error (`check.lifecycle-transition-invalid`, "recorded lifecycle transition 'to-review' ->
'draft' is invalid") the moment a third record was appended, because the parser reads a date group
forward. Swapped; `check_lifecycle_transitions` now reports nothing for this plan. The `reviewed`
transition itself was written through `aw ipd set reviewed` rather than by hand, so the tooled record
exists beside the narrative line.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric C/D, GUIDING_PRINCIPLES P16 | `.aw/records/plans/pending/20260930-xi5jt0-01-90z361-...ipd.md` E-03 and F-11; `.aw/records/plans/pending/20260928-structpin-01-b02ohu-...ipd.md` E-02/E-04/E-05/E-06; `.aw/records/plans/pending/20260928-structpin-02-76ic0k-...ipd.md` E-01; `GUIDING_PRINCIPLES.md` section 16 | E-03 instructed the executor to REUSE the shipped `ast.parse` walk in `tests/test_runner_shared.py` (and to extract it to a module-level helper). APPROVED sibling `b02ohu` rewrites that exact helper onto `vars()` and requires a pasted search proving ZERO `ast.parse`/`ast.walk`/`ast.unparse` remain in that file; approved `76ic0k` ships a guard refusing a new one; P16 prohibits AST reads of production code with no enumeration-only carve-out and separately forbids placement pins via "module dictionaries". The plan's F-11 had dismissed both siblings as prose-only, which reading their E-items refutes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 rewritten onto `vars()` with the mechanism demonstrated green and red at review (new F-13); F-11 corrected and superseded by new F-12; `- Item-Dependencies:` changed from `none` to `executed:b02ohu`; E-04 re-homed into the new test instead of the `b02ohu`-edited one; a third STOP directive and a required AST search added. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric D (anti-regression), internal consistency | E-01's comment instruction; V-04's own demonstration requirement | E-01 told the executor to write that the shared constant's value is "enforced by the E-03 guard". E-03 is structurally BLIND to a drifting SHARED value: after E-02 both hosts read it, so they continue to agree with each other. E-04 is the guard that catches it, which V-04 already demands a demonstration of. The plan contradicted itself between an E-item an executor follows and a V-item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now cites E-04, and states why E-03 cannot serve, pointing at V-04's paired-mutation demonstration. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (testing), live-artifact re-derivation convention | Plan F-10; `python3 -m pytest` at review HEAD `e4474af7` | F-10's baseline `3387 passed, 2 skipped` is stale, and the tree is NOT green: the same command reports `1 failed, 3414 passed, 2 skipped`, the failure being an unrelated date-rollover flake in `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`. V-04 demanded "at least the F-10 baseline ... plus the new tests", an unsatisfiable bar that would make an executor either misattribute a pre-existing red or paper over it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 records the measured tail and names the failure; `## Required tests` and V-04 now require re-deriving the baseline before and after and attributing any failure present in both, with the bar being no regression in or reachable from the four Scope-Paths. The fork-scan baseline is likewise re-derived rather than trusted. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (executability), honest bounds | Plan E-03 and OQ-01 ("covers all eleven"); `isupper()` probe; `vars()` identity partition | E-03's coverage claim was wrong in one direction and silent in another. It asserted the guard "compares every co-defined host-invariant constant" so all eleven F-09 names are covered; `"_close_process_streams".isupper()` is False, so an `isupper()` filter reaches only ten, nine of them needing coverage. Separately the `vars()` enumeration reaches 57 names of which 48 are the same object, so the sweep is mostly vacuous by construction and said nothing about it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14 measures both bounds; E-03 must state them in the test docstring and is explicitly forbidden from asserting a count (which would be the census pin P16 forbids); OQ-01's claim corrected from eleven to nine with the exclusion explained. |
| PR-005 | LOW | IN-SCOPE | Rubric A (correctness of a stated reason) | Plan deferral row and OQ-01; `re.Pattern.__eq__` probe on four interpreters; `pyproject.toml` `requires-python`; `.github/workflows/tests.yml` matrix | The deferral of `_ID_RE`/`_STATUS_RE` rested partly on "they are compiled patterns", implying comparison is unsound or awkward. `re.Pattern` implements value equality on every interpreter in the declared `>=3.9` support matrix, so the sweep compares them soundly and non-vacuously. The deferral is still right; its stated basis was not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-16 records the four-interpreter measurement; the deferral row and OQ-01 now rest on WHERE a pattern should live rather than on comparability, and say so explicitly as a correction. |
| PR-006 | LOW | IN-SCOPE | Rubric G, self-defeating acceptance criterion | Plan E-03 as authored ("naming them explicitly rather than computing the expectation") | E-03 required the compared name list to be HAND-SPELLED as the F-09 set. A hand list cannot see a constant added later, which is precisely the drift the guard exists to catch, so the instruction would have shipped a guard that silently stops covering new constants. The anti-self-reference concern behind it is legitimate but is already met by an independently spelled exemption set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The hand-list instruction is explicitly WITHDRAWN in E-03 with the reason stated; the authored expectation is now `EXPECTED_HOST_VARYING = {"DEPENDENCY_BLOCK_RECOVERY_HINT", "FULL_AUTO_ACTOR"}`, which the sweep must assert are STILL UNEQUAL so the exemption cannot go vacuous; V-03 requires the set be pasted as committed. |
| PR-007 | LOW | IN-SCOPE | Project convention (newest-first history), `aw check` I-03 | Plan `## Workflow history`; `check_engine.check_lifecycle_transitions`; `ipd_lifecycle._plan_status_event_groups` | The two 2026-09-30 history records were in oldest-first order (`draft` above `to-review`), inverting the documented newest-first convention. Latent while the group was unordered, it became a real `check.lifecycle-transition-invalid` error ("'to-review' -> 'draft' is invalid") as soon as a third record was appended, because the checker reads each date group forward. Also F-07's "19 co-defined" count omits two non-`isupper()` names. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The two records swapped into newest-first order; `check_lifecycle_transitions` now reports nothing for this plan. The `reviewed` transition was written via `aw ipd set reviewed` so a tooled record exists beside the narrative line. F-07 now states 19 `isupper()` / 21 including the two non-upper names. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should E-03 enumerate with an AST walk (as authored) or with `vars()`? | `vars()`, with no AST use of its own. | (a) Keep the AST walk and argue enumeration is not verification, so P16's prohibition does not reach it. REJECTED: P16 forbids `ast.parse` against production code without qualification and separately forbids inspecting "module dictionaries" for placement, so the carve-out would have been invented here; and two APPROVED plans (`b02ohu` removing every `ast.*` from this exact file, `76ic0k` refusing a new one) would revert then refuse it. (b) Keep the AST walk but exempt it in `76ic0k`'s allowlist. REJECTED: that plan's own review recorded an allowlist entry as a claim that a file holds a SANCTIONED pin, which this would not be. | `GUIDING_PRINCIPLES.md` section 16; `b02ohu` E-04/E-05/E-06; `76ic0k` E-01; demonstrated replacement in F-13 (55 compared, GREEN; mutation RED with both values; restore GREEN). | yes |
| D-2 | Must this plan wait for `b02ohu` to execute, or may it run independently? | Wait: declare `- Item-Dependencies: executed:b02ohu`. | Declare no dependency and rely on the runner's isolated worktrees to merge both. REJECTED: isolation prevents a textual conflict, not a logical one. `b02ohu` E-04/E-06 require a pasted search showing ZERO `ast.*` in `tests/test_runner_shared.py`, so even the `vars()` version is safer landing after it, and landing first with any AST walk would have put that plan's executor in front of a file it must prove clean. | `b02ohu` front matter (`- Status: approved`, `- Scope-Paths:` includes `tests/test_runner_shared.py`) and its E-04/E-06 expected outcomes; recorded in the plan as OQ-02. | yes |
| D-3 | Where should E-04's by-value assertion live: in the shipped `test_set_plan_approved_durable_history_pin` (as authored) or in E-03's new test? | In E-03's new test. | Add to the shipped test. REJECTED: `b02ohu` E-02 edits that exact test (removing its two `inspect.getsource` lines), so adding there widens the collision surface on a shared file for no benefit. | `b02ohu` E-02 read in full; this plan's `- Scope-Paths:` already covers the file either way. | yes |
| D-4 | Is the V-04 bar "at least the F-10 baseline plus the new tests" acceptable given the tree is not green? | No; replace it with re-derive-before-and-after plus explicit attribution of any failure present in both runs. | (a) Keep the authored count. REJECTED: stale by 27 tests and unsatisfiable while one unrelated test fails. (b) Require the suite be green. REJECTED: that makes an unrelated date-rollover flake in the backlog setter block this plan, which is not this plan's defect to fix. | `python3 -m pytest` at review HEAD: `1 failed, 3414 passed, 2 skipped`; the isolated failure's `- 2026-09-30` / `+ 2026-10-01` diff; `date -u +%F` -> `2026-10-01`; the live-artifact re-derivation convention in the plan-review rubric. | yes |
| D-5 | Does the `_ID_RE`/`_STATUS_RE` deferral survive once compiled-pattern comparability is measured? | Yes, the deferral stands, but its stated reason is corrected. | Re-open the deferral and sweep them in. REJECTED: comparability was the only part that was wrong; the placement judgement and the durable-history argument that bounds this plan are both untouched, and the carrier item `kz4j7o` already owns the sweep. | Four-interpreter `re.Pattern` equality probe (3.9.25 / 3.11.15 / 3.12.3 / 3.14.6); `pyproject.toml` `requires-python = ">=3.9"`; `.github/workflows/tests.yml` matrix; recorded as F-16. | yes |
| D-6 | Should the inverted 2026-09-30 history records be repaired in place, or left and noted? | Repaired in place (swapped into newest-first order). | Leave them and note the inversion. REJECTED: the plan is in `pending/` and not terminal, so nothing in it is a protected record of work performed; and leaving it means `aw check` reports an `error`-severity `check.lifecycle-transition-invalid` against the plan, which fails closed in CI. | `check_engine.check_lifecycle_transitions` (scoped to pending plans only, explicitly grandfathering terminal ones); `ipd_lifecycle._plan_status_event_groups` showing the group read forward; verified NONE after the swap. | yes |

No decision in this round is `Reversible: no`, so none requires escalation beyond this record. No finding
was left `OPEN` or `DEFERRED`, so no `- Blocking: yes` escalation is owed under the gate threshold.
