# Review findings: plan qgpanb

- Subject-Id: qgpanb
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `512464cc`. The plan file was committed and unmodified
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0) carrying one advisory `IPD-Z602`, and
`--phase review-finalize` reports `clean` with the same advisory after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

THE CENTRAL ANALYSIS IS CORRECT AND UNUSUALLY WELL EVIDENCED. I re-drove every finding rather than
trusting it, and the plan's own self-correction of its backlog item is its best work:

- F-01 reproduces exactly. The registry holds 56 rules, all five ids are absent, and each resolves
  through `rule_spec` to `RuleSpec(severity='error', assurance='repository',
  determinism='deterministic', invariant='')`.
- F-02 reproduces, and its reasoning is confirmed to live where the plan says: `lane_drift_severity`'s
  own docstring states the superseded exemption ("failing the gate on it would assert a loss that did
  not happen"). The live tree carries 4 `attention.lane-stranded` stamped `error` and 1
  `attention.lane-superseded` stamped `info`, and `drift_exit_code` over that drift returns 1.
- F-03, THE MOST IMPORTANT FINDING IN THE PLAN, REPRODUCES IN BOTH DIRECTIONS. Registering all three
  research/plans rules at `info` and changing nothing else left `aw index research --check` at exit 1.
  Applying `enrich_drift` to those findings took `artifact_core.drift_exit_code` from 1 to 0. The raw
  stamped severity of all three is `''` while the neighbouring `check.stale-index-missing` arrives
  stamped `'info'`, which is exactly the asymmetry E-04 closes. So registration alone really is inert,
  E-04 really is required, and the plan is right to call itself a gating change rather than
  bookkeeping. This is the plan correcting its own backlog item's premise, with the measurement to
  back it.
- F-05's striking pair reproduces for the stated reason: `check_engine.check_content` reaches
  `research_index.check_drift` only under `if dirs and include_retired:`, so default `aw check
  research` exits 0 while `aw index research --check` exits 1 over the same tree.
- F-06 reproduces verbatim in `research_refs`: `exit_code = 1 if danglers else 0` plus a hardcoded
  `severity="error"`, never consulting the registry.
- F-07, F-09, F-10 reproduce exactly: 56 rules at 33 `error` / 12 `warning` / 11 `info`, zero
  severities outside the three-value enum, no registry key containing `graduation` or `duplicate`, and
  both shipped guards green (`tests/test_check_engine_spec_criteria.py` plus
  `tests/test_work_gate_severity.py`, 26 passed).

EVERY FINDING I RAISED IS IN A VALIDATION BAR, NOT IN THE ANALYSIS. That distinction matters for how
the plan should be read: its reasoning about severity, about the registry/emitter split, and about why
`info` is the only advisory tier all survived scrutiny intact. What did not survive is three
authored-at-a-moment figures that the validation items had hardened into pass/fail gates.

THE DOMINANT FINDING IS A BASELINE THAT HAS ALREADY MOVED, AND THE RULE BUILT ON TOP OF IT (PR-001).
`aw index plans --check` exits 1 at this HEAD, not the 0 F-05 recorded, because the plans manifest went
stale and `plans_index.check_drift` emits 2 `check.stale-index-stale` findings. The number itself is
harmless; E-06's rule is not. E-06 said any OTHER surface moving is a FAILED reconciliation and V-06
permitted EXACTLY TWO movements, so an executor diffing its own baseline against the written F-05
numbers would either report a false failure or run `aw index plans` to "restore" the baseline, writing
a manifest the plan does not declare in `- Scope-Paths:`. Both items now compare against the E-01
baseline only, and the regenerating-verb shortcut is named and forbidden.

I ALSO FOUND A DEMAND THE TREE CANNOT SATISFY (PR-003). E-04 is right that the plans-side
`dangling-citation` construction must be wrapped, but that site emits ZERO findings here, so no
behavioral demonstration of it is possible; V-04 asked for one implicitly while also enumerating five
sites under the word FOUR. Now stated plainly: four research sites plus one plans site, the plans one
verified by diff, with an explicit instruction not to manufacture a plans dangler to exercise it.

OQ-01 IS CORRECTLY LEFT TO THE APPROVER AND I DID NOT RESOLVE IT. Whether `dangling-citation` should be
`info` (making 4 genuine dangles advisory alongside the placeholder noise) or stay `error` with
`EXAMPLE_ID6S` extended is a risk-appetite call, the plan writes both branches out with the re-scope
instruction, and `Blocking: no` is right because the registration lands either way. Re-measured at
review: 27 distinct dangling ids, of which the top five are placeholders, against an allowlist holding
exactly two entries.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E (testing/verification); G (live-artifact criteria) | plan F-05 row, E-06, V-06; `agent_workflows/plans_index.check_drift` | An authored baseline exit code has ALREADY moved: `aw index plans --check` exits 1, not the 0 F-05 recorded, because the plans manifest is stale and `plans_index.check_drift` emits 2 `check.stale-index-stale` findings (a registered `warning`, which fails the gate exactly as `error` would). E-06's "any OTHER surface whose exit code moves is a FAILED reconciliation" and V-06's "EXACTLY TWO movements are permitted" turn that ordinary drift into a false failure, and the tempting repair (`aw index plans`) writes a path this plan does not declare. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 and V-06 now compare against the E-01 baseline ONLY, never against F-05's written numbers, with the regenerating-verb shortcut explicitly named as a FAILED V-06. V-06's permitted movements reduced from two to the one actually predicted. F-05 restated so every number in it is context and the per-surface shape is the durable part. F-11 added with the measurement. |
| PR-002 | MEDIUM | IN-SCOPE | E (testing/verification) | plan E-06 Expected outcome, V-06, Required tests item 1; `agent_workflows/backlog.py` local clock versus `agent_workflows/status_set.py` UTC | E-06 demands "a bare full-suite pass" and V-06 its `N passed` line, but the suite is NOT green: `1 failed, 3480 passed, 2 skipped`, failing `test_release_exempt_setter_roundtrip_and_parity` on the pre-existing local-versus-UTC history-date skew (`TZ=UTC` passes; filed as `fnb8pl`, `lq2w86`, `2wae2x`, all release-gated, owned by another party). An executor cannot satisfy the bar honestly and might try by touching a co-worker's gated test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06, V-06 and Required-tests item 1 rewritten to an unchanged NAMED FAILURE SET re-derived at E-01, with the pre-existing failure named and both the fix and a `TZ` workaround forbidden under the shared-checkout rule. F-12 added. |
| PR-003 | LOW | IN-SCOPE | E (testing/verification); G | plan E-04, V-04; `agent_workflows/plans_index.check_drift` | E-04 correctly requires wrapping the plans-side `dangling-citation` construction, but that site emits ZERO findings on this tree, so it cannot be demonstrated behaviorally and nothing in the plan says so; an executor could read an empty result as a failed wrap or go hunting for a plans dangler. Separately V-04 says the diff "must show FOUR construction sites ... plus the plans `dangling-citation` site", enumerating five items under the word FOUR. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states the plans site is wrapped blind, why that is correct, and that no plans dangler may be manufactured; the site count is stated as FIVE (four research plus one plans) in both E-04 and V-04, and V-04 requires the plans site be verified by diff rather than behaviorally. F-13 added. |
| PR-004 | LOW | IN-SCOPE | G (live-artifact criteria) | plan F-01 and F-04 rows | Two corpus figures drifted between authoring and review: `dangling-citation` is 69 findings over 27 distinct ids (authored 61 over 23), and the plans/backlog split is 64/5 (authored 56/5). The rows half-acknowledged drift but still led with specific numbers, which is the shape the repository's live-artifact convention warns about. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 re-measured with the qualitative shape (placeholder dominance, archive concentration, housekeeping details) stated as the finding and every count explicitly context, noting E-01 re-derives them and no `V-*` item asserts any. The `adopted-without-consumer` 35/17 and `stale-state-to-promote` 17 figures reproduced exactly and are recorded as such. |
| PR-005 | LOW | UNDER-SCOPE | C (architecture); G | plan Scope check; nineteen pending plans declaring `agent_workflows/check_engine.py` | The Scope check asserts "Over-scope: none" and the lifecycle note asserts the three topically related plans "all edit DIFFERENT files", but no survey of who else declares these paths was recorded. `check_engine.py` is declared by nineteen pending plans, ten already `approved`, and one plan (`ucwlwt`) names all three of this plan's research rules, so a reader cannot tell from the plan whether that was checked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a CROSS-PLAN FILE SHARING row to the Scope check recording the survey and its result: nineteen declarers make overlap unremarkable (runner isolation plus merge-and-revalidate is what makes it safe), no sibling touches these five ids, and `ucwlwt` adds a NEW rule while stating it changes no existing rule, so no `- Item-Dependencies:` edge is owed. Instructs re-checking at execution, pointing at E-01's existing STOP-AND-REPORT condition as the live guard. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | An authored baseline exit code has already moved and a validation rule treats any movement as failure. Update the number, or change the rule? | CHANGE THE RULE: compare against the E-01 baseline only, and forbid "restoring" a baseline with a regenerating verb. | (a) Just update F-05's numbers to today's - rejected: it fixes one instance of a recurring problem and the next drift reintroduces it; these are live populations and the plan already instructs E-01 to re-derive them, so the defect is that V-06 then contradicts E-01 by pinning the authored values. (b) Drop the surface comparison - rejected: it is the plan's only evidence that a deliberate gate relaxation did not relax more than the three rules named, which is the whole risk of the change. (c) Add `aw index plans` to Scope-Paths so the baseline can be restored - rejected outright: regenerating a manifest is unrelated work, writes a path no E-item owns, and would make the plan's diff include a generated file. | measured `aw index plans --check` exit 1 with its 2 `check.stale-index-stale` findings versus F-05's recorded 0; E-06's own "any OTHER surface" rule and V-06's "EXACTLY TWO movements"; the plan's existing E-01 instruction to re-derive all eight surfaces. | yes |
| D-2 | E-04 must wrap a construction site that produces no findings here. Keep it, drop it, or demand a demonstration? | KEEP the wrap, verify it by DIFF, and state plainly that no behavioral demonstration is possible or required. | (a) Drop the plans site from E-04 - rejected: the rule's severity must be registry-governed wherever it fires, and leaving one emitter unstamped recreates exactly the split E-04 exists to close, silently, for whenever a plans dangler next appears. (b) Require a behavioral demonstration - rejected on measurement: `plans_index.check_drift` returns only `check.stale-index-stale` here, so satisfying it would mean fabricating a dangling plan citation, which writes records outside the fence to exercise a code path the diff already proves. (c) Leave V-04 ambiguous - rejected: the ambiguity is what would send an executor hunting, and the FOUR-versus-five miscount compounds it. | `plans_index.check_drift(repo, .aw/records/plans)` returning `Counter({'check.stale-index-stale': 2})` with zero `dangling-citation`; the single `_core.Drift(..., "dangling-citation", f"PLAN-{d.id6}")` construction confirmed present; the research-side site count of four verified by reading `research_index.check_drift`. | yes |
| D-3 | OQ-01 asks whether `dangling-citation` should be `info` at all. Resolve it from evidence, or leave it to the approver? | LEAVE IT to the approver, unchanged and non-blocking. | (a) Resolve it to `info` on the corpus evidence - rejected: the measurement establishes that MOST findings are noise, not that making 4 genuine dangles advisory is acceptable, and that second step is a risk-appetite judgement about a gate the maintainer owns. (b) Resolve it to `error` plus an allowlist extension - rejected: it is the bigger change the plan itself identifies, needs a per-token justification for roughly 19 additions by the allowlist's own rule, and is a different plan. (c) Mark it `Blocking: yes` - rejected: both answers leave the deliverable intact (the registration happens either way and only one rule's tier is in question), so blocking would stop a plan that is ready on every other axis, and the plan already writes the re-scope instruction for the alternative. | re-measured 27 distinct dangling ids with the top five being documentation placeholders against `EXAMPLE_ID6S` holding exactly `frozenset({'k7m2xq','ab12cd'})`; the plan's own written alternative and re-scope instruction; `plan-review`'s rule that a non-blocking open question does not make a plan NO-GO (maintainer ruling 2026-09-10). | yes |
