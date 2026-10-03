# Review findings: plan fqcax0

- Subject-Id: fqcax0
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201 (MEDIUM, fixed), PR-202 (MEDIUM, fixed), PR-203 (MEDIUM, fixed), PR-204 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `cebbcd0f6`. The plan file was committed and the tree clean,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize` reports
`conforming` after revision. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407`
orchestrator child-row check does not apply.

THIS IS THE BEST-EVIDENCED PLAN IN THIS SWEEP AND ITS FINDINGS SURVIVED EVERY INDEPENDENT CHECK I COULD
MAKE. I re-derived each load-bearing claim rather than trusting it, and all of F-01 through F-15 reproduce:

- F-01 reproduces through the library on a real plan: a `- Date: 2026-07-23 (fleshed later)` lints
  `conforming` with ZERO diagnostics, while the same plan with the line deleted yields `error` with
  `IPD-M101`. Corrupting a required field is silent; deleting it is caught.
- F-02 reproduces: `ipd_schema.META_REQUIRED` contains `Date`, and `validate_metadata`'s source mentions
  `Date` zero times outside the presence loop.
- F-03 reproduces on all five consumers: `plans_refs._plan_date` and `plans_archive._plan_date` both
  return the literal `20260101`; `check_engine._plan_date_compact` returns `None`;
  `ipd_lint._m105_terminal_date_applies` returns `False`; and `_citation_anchor_applies` goes `True` on a
  good date to `False` on the malformed one.
- F-10 reproduces exactly, including the detail that makes it bite: `2026-13-45` yields `20261345` from
  both `plans_refs._plan_date` and `check_engine._plan_date_compact`, shard `202613` from
  `artifact_core.shard_for_date`, and `0.0` from `plans_archive._age_days`, so an impossible date reads
  as authored today and is never sweep-eligible.
- F-11 reproduces and is the sharpest finding in the plan: `date.fromisoformat('2026-W01-1')` returns
  `2025-12-29` and `date.fromisoformat('20260929')` returns `2026-09-29`, so the obvious primitive admits
  both shapes the shape check exists to refuse.
- F-07 reproduces: the `qrokie` casualty lints `legacy/not evaluated` with an empty diagnostic list.
- F-09 reproduces: both templates carry `- Date: <YYYY-MM-DD>` on line 3.
- F-12 reproduces: `tests/test_ipd_set_plan.py` carries the only `- Date: 20260823` and imports only
  `ipd_set_plan` and `orchestrate_isolation`.
- F-13 reproduces: Section 4.4's "Field rules" list gives value rules for `Kind`, `Status`, `Set` and
  `Order` and says nothing about `Date`; Section 16.1 carries the "invalid or missing required metadata
  field" bullet.
- F-14 reproduces: `ipd_lint.check_metadata`'s chain is verbatim as described, with `C_META_FIELD`
  (`IPD-M104`) as the else branch and `"missing" in me.message` selecting `IPD-M101`.
- OQ-03's premise reproduces: 40 of 688 clustered Sets carry members with differing leading dates (31 of
  589 at authoring), so a naive filename-versus-metadata equality rule would still fire on dozens of
  healthy Sets.

I ALSO PROTOTYPED THE ENTIRE FIX INDEPENDENTLY, which is the strongest confirmation available short of
executing the plan. Monkeypatching E-03's exact check (ISO shape plus explicit `datetime.date(y, m, d)`,
exempting the literal `<YYYY-MM-DD>`, message free of the substring `missing`) and driving
`ipd_lint.lint_text` at `checkpoint="author", directory="pending"`: the good control stays `conforming`
with zero diagnostics; all five malformed shapes flip to `error` carrying exactly `IPD-M104` and NOT
`IPD-M101`; the placeholder stays `conforming`; and both byte-pinned templates stay `conforming` with
zero diagnostics. Then a full before/after author-phase sweep over all 1143 tracked `.ipd.md` files
reported `CHANGED diagnostic sets: 0`. Recorded in the plan as F-17.

One thing worth naming as correct rather than as a finding: the plan was authored with NO `- Readiness:`
field and says so explicitly in its gate, which is exactly what AGENTS.md requires (the field is an
output of `/plan-review`, and a hand-written value forges the attestation the auto-approve predicate
reads). That is the right posture and few plans state it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | MEDIUM | IN-SCOPE | E (testing); G (live-artifact criteria) | review scan of every `.aw/records/plans/**/*.ipd.md` first `- Date:` line: `1143 total, 1142 ISO, 0 compact, 1 malformed`, per-directory `{executed: 910, superseded: 38, pending: 190, not-executed: 5}` | E-04's Expected outcome and V-04's Required evidence both name the literal triple `1089 well-formed, 1 malformed, 0 compact` (and "187 pending") as the expected post-change breakdown. Those are live-population counts and had already drifted to `1142/1/0` and 190 pending by review two days later, so an executor comparing against the literal would report a false disagreement on a healthy tree. The plan's own instruction to re-measure is right; the literal expectation contradicts it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-16 records the re-measurement and, more importantly, that every INVARIANT held: exactly one malformed file, still the same `qrokie` casualty, still the only `20260101-` prefixed plan, zero compact, zero malformed pending. E-04 and V-04 rewritten to RE-DERIVE the breakdown and report it as context, with the bar restated as two invariants (one malformed file; that file in a terminal directory). The ZERO-changed-file expectation is untouched and was independently confirmed over 1143 files (F-17). |
| PR-202 | MEDIUM | IN-SCOPE | G (plan executability) | `.aw/records/plans/executed/20260929-j84jg3-01-949enf-...ipd.md` with `- Status: executed`; `inspect.getsource(plans_refs._plan_date)` still showing `return "20260101"`; `inspect.getsource(plans_refs._preserved_date)` docstring | The Deferred entry describes `949enf` as "already carried and in review". It has EXECUTED. Left uncorrected, a reader could conclude the consumer half is unfixed in general, or conversely that it is fully fixed and this plan's under-scope disclosure is stale. Neither is right, and the truth strengthens the fence: `_plan_date`'s `20260101` fallback is still there, `949enf` added `_preserved_date` which reaches it only last, and that function's docstring cites THIS defect as its reason ("its own failure mode is a FABRICATED CONSTANT ('20260101') rather than an absent value (and a malformed - Date: escapes lint without complaint)"). So an executed plan's shipped comment asserts the gap this plan closes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-18 records the status, the surviving fallback, and the docstring. The Deferred entry's wording corrected and its `Carrier-Evidence` confirmed to resolve. The fence is UNCHANGED: `plans_refs.py` stays out of `- Scope-Paths:` and the under-scope disclosure stays literally true. |
| PR-203 | MEDIUM | UNDER-SCOPE | A (correctness); G | `grep -n 'Required fields (all IPDs)'` on the spec returning six fields beside `ipd_schema.META_REQUIRED == ('Date', 'Kind', 'Concern', 'Scope', 'Status', 'Author', 'Id')`; `grep -n '\`Id\`'` over the spec finding no required-field claim; `grep -rln META_REQUIRED` over pending plans and open backlog matching only this plan and `fhinri` | Section 4.4's required-fields ENUMERATION is also wrong, two paragraphs above the list E-05 edits: it omits `Id`, which the linter enforces, and the spec claims `Id` is required nowhere. The drift is unowned by any pending plan or open item. This is a real hazard for THIS plan specifically: an executor amending Section 4.4 will read the adjacent wrong sentence and may "helpfully" correct it, which would change a second spec contract undeclared and surface only at scope reconciliation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-19 records it with the measurement. E-05 given an explicit instruction to amend the "Field rules" list ONLY and to leave the enumeration byte-unchanged, with the reason stated (a different sentence making a different claim; an undeclared second contract change is what the reconciliation gate exists to surface). Added to Deferred as `Carrier-Declined` rather than carried, because filing an item is a maintainer judgement: the drift is in an `implemented` spec's prose, breaks no behavior since the linter is the authority, and may be a deliberate omission from when `Id` was introduced. |
| PR-204 | LOW | IN-SCOPE | E (testing) | review bare run: `3665 passed, 2 skipped, 3 warnings in 120.85s` at HEAD `cebbcd0f6` versus F-08's `3387 passed`; targeted `tests/test_ipd_schema.py tests/test_ipd_lint.py tests/test_ipd_templates.py -o addopts=""` reporting `91 passed` | The plan already tells the executor to measure their own baseline and NOT to compare against F-08's `3387`, which is the correct instruction and better than most plans manage. What was missing is the confirmation that the drift it anticipates is real (278 tests in two days), and a targeted command for the three modules this plan touches or constrains, which is the fastest signal that the placeholder exemption and both new surfaces are right. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The review baseline added beside F-08's as the evidence that the anticipated drift happened, and a targeted three-module command added to Required tests with its `91 passed` review figure, so the executor has a fast check before paying for a full bare run. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The `Id` required-fields drift (PR-203) is a real spec error adjacent to E-05's edit. Fold the correction into E-05, file a backlog item, or record and decline? | RECORD and DECLINE, with an explicit instruction to E-05 not to touch it. | (a) Fold the one-word correction into E-05, since the executor is already editing that section. (b) File a backlog item for it. | (a) is refused on this repository's own stated rule, which this plan is otherwise scrupulous about: a plan may amend a spec but MUST declare it, and the declaration is what makes the amendment visible to the run's spec-edit announcement and the finalize reconciliation. The required-fields ENUMERATION is a different claim from a `Date` VALUE rule, so correcting it silently would change a second contract undeclared, and "the executor is already in the file" is exactly the reasoning that makes scope fences leak. (b) was close and I chose against it only because the drift breaks no behavior (the linter is the authority and already enforces `Id`) and may be deliberate, so filing it asserts a defect judgement that is the maintainer's; the measurement is recorded where the next author of that sentence will find it. | yes |
| D-2 | The corpus triple drifted (PR-201). Update it to the review figures, or remove it as a bar? | REMOVE it as a bar; keep both measurements as context and assert two invariants instead. | (a) Replace `1089/1/0` with `1142/1/0`. (b) Delete the breakdown entirely. | (a) reproduces the defect on a two-day clock, which is measurable: the figure moved 53 in two days and this plan will sit in `pending/` awaiting approval. The workflow's live-artifact convention names this exact pattern. (b) loses the information that actually licenses the change, which is not the count but the SHAPE: one malformed file, in a terminal directory where the linter never reaches a metadata check. Asserting the invariants keeps the licence and drops the drift. | yes |
| D-3 | Is OQ-03's `deferred` status with `Owner: maintainer` legitimate, or is it an unresolved question that should block? | LEGITIMATE as deferred and non-blocking; left as written. | Escalate it to `Blocking: yes` so a human must answer before execution. | Escalation would be wrong on three grounds, each checkable. The question is about a DIFFERENT rule (a disagreement between two individually well-formed sources) rather than this plan's subject (one unparseable value), so this plan stands alone regardless of how it is decided. It is FILED rather than stranded in prose: backlog `mt6j1p` exists, is `open`, carries `followup`/low, and its body names this plan and OQ-03 as its origin, so the deferral is tracked. And its design question is genuinely the maintainer's: a naive equality rule would fire on 40 of 688 healthy clustered Sets (re-measured at review), because spec `agents-artifact-organization` 4.2 makes the leading date set-canonical, so the false-positive profile must be settled by someone who owns the policy. | yes |
| D-4 | Is the plan's `IPD-M104`-not-a-new-code choice (OQ-02) sound? | SOUND; left as written, and independently verified. | Recommend a dedicated code so a consumer can route on a malformed-date refusal. | The plan's own reasoning applies the module's stated test correctly: `C_SETID_LENGTH`'s comment earns a dedicated code because its rule has a specific mechanical remedy, and "fix the value" is not one. I additionally VERIFIED the consequence that makes the choice safe, which the plan asserts and I did not want to take on trust: under the prototyped check all five malformed shapes land on `IPD-M104` and none on `IPD-M101`, so the message-substring routing constraint E-03 carries is both real and satisfiable. | yes |
