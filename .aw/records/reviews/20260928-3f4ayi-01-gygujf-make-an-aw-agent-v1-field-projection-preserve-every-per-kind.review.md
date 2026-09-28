# Review findings: plan gygujf

- Subject-Id: gygujf
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fdb207d7` in a lane worktree; the plan was authored against `71aee0d3`. Structural
preflight `aw ipd lint --phase author --agent` CONFORMED before revision (exit 0, two `IPD-Z602`
advisories, both pre-existing on E-01 and E-04); `--phase review-finalize --agent` conforms after
revision with one advisory remaining (E-01 only, since the revision cleared E-04's). No pre-review
snapshot was owed: the plan was committed and unmodified with `git status --porcelain` empty at review
start. The plan carries `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. Every
measurement was taken by importing the package and probing in-process, plus four live CLI runs; nothing
was written outside this lane.

THE DIAGNOSIS IS TRUE AND BOTH INSTANCES REPRODUCE EXACTLY. F-01's reproduction raises the quoted
`ValueError: Invalid aw.agent/v1 record: Summary record missing required field 'total'; ... 'emitted';
... 'omitted'` verbatim. F-03, which is the plan's own contribution over its backlog item, reproduces
end to end through the ordinary renderer path: `AgentRenderer().render(CommandResult(..., complete=False,
applied=False), ctx)` emits a valid record with no `fields` and raises `Greenwash violation: outcome
cannot be 'clean' when complete=False` with `fields=['findings']`. F-05's masking analysis is right in
detail: all four `--fields` leaves emit valid records today, and `aw runs export`'s preview really does
carry `applied: false` with `complete: true`, which the greenwash rule does not police. The plan's
central judgement, fix (a) over fix (b), is correct and well argued.

THE DOMINANT FINDING IS THAT E-01's THIRD ASSERTION, THE ONE THE WHOLE DURABILITY ARGUMENT RESTS ON,
WAS SPECIFIED SO THAT IT PASSES ON TODAY'S BROKEN CODE. It said to project with `filter_record_fields(record,
fields=[])`, and that function opens `if not fields: return dict(record)`. So `fields=[]` returns the
record UNCHANGED, every required field is trivially still present, the derivation reports nothing, and
the assertion is GREEN before the fix. Measured: with `fields=[]` the derivation catches nothing, while
with `fields=['cmd']` it catches `total`, `emitted`, `omitted`. This is worse than a weak test, because
the plan explicitly presents this assertion as what makes the fix durable against a future validator
rule (F-06) and requires V-01 to paste its red output as the non-vacuity proof. An executor writing it
as specified would find it green pre-fix, and the most likely reactions are both bad: conclude the
defect is already fixed, or delete the assertion as broken.

THE SAME ASSERTION HAS A SECOND, INDEPENDENT VACUITY THAT SURVIVES FIXING THE FIRST. Single-field
deletion catches `applied` only on a record where `applied: false` is the SOLE greenwash exemption.
`is_preview = outcome == "preview" or record.get("applied") is False`, so on a `preview`-outcome record
the exemption already holds via the OUTCOME and deleting `applied` leaves the record valid. Measured on
two otherwise identical records: `outcome=preview` derives `[]`, `outcome=clean` derives `['applied']`.
A corpus built from the natural-looking preview shape therefore pins `total`, `emitted` and `omitted`
while silently leaving `applied` unpinned, which is exactly the field F-03 exists to protect.

THE THIRD FINDING IS THE SUITE BASELINE, AND IT IS INVERTED RATHER THAN MERELY STALE. F-09 told the
executor to expect one failing test, to compare against `1 failed, 3034 passed, 2 skipped`, and that a
green line "would itself need explaining". Commit `f1b5b9ff` fixed that test by replacing the live-state
token with the synthetic `executed:aaa111`, which is precisely the remedy carrier `03aicr` proposed; the
bare suite now reports `3075 passed, 2 skipped` with zero failures. As authored, the plan teaches an
executor to accept a red suite on a named test and to distrust a green one. It also leaves carrier
`03aicr` stale while still `open` and still carrying `- Blocks-Release: next`, so a release is gated on
work already done. The review does NOT close that item (another party's item, and a gated close has its
own predicate); E-04 now requires the divergence reported.

WHAT THIS REVIEW STRENGTHENED RATHER THAN CORRECTED. The plan claims its fix is sufficient on a sampled
corpus; it is provably COMPLETE at this HEAD. Extracting every name `validate_agent_record` reads from
its own source yields exactly eleven, and E-02's union covers all eleven with nothing left over (F-13),
which also gives E-01's derived property its real job: firing when a twelfth appears. The reverse risk
was probed too, since "preserve more" is not automatically safe when a retained field can invalidate a
record (the summary count-consistency rule is that shape): both adversarial cases stay valid under the
wide set (F-14).

WHAT THIS REVIEW DID NOT CHANGE. The route, the fix choice, and both OQ resolutions stand. OQ-01's
rejection of fix (b) is correct and rests on F-03, which reproduced. The decision not to restructure the
validator into a declarative table stands, and its reasoning (the greenwash rules are conditional and do
not reduce to a per-kind list without losing fidelity) is confirmed by F-13's extraction, which shows
`applied` is consulted unconditionally by name while its EFFECT is conditional. The `run_analytics_cli`
deferral, the three-carrier posture, F-10's no-change-without-fields conclusion, and the no-spec-amendment
argument all hold.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | BLOCKER | IN-SCOPE | E. Testing and verification | `agent_schema.filter_record_fields`'s opening `if not fields: return dict(record)`; review probe on the summary record printing an EMPTY derivation for `fields=[]` beside `['total','emitted','omitted']` for `fields=['cmd']`; plan E-01 assertion 3 as authored ("then `filter_record_fields(record, fields=[])` still contains `k`") | **E-01's DERIVED PROPERTY, THE ASSERTION THE PLAN'S WHOLE DURABILITY ARGUMENT RESTS ON, PASSES ON TODAY'S BROKEN CODE AS SPECIFIED.** `fields=[]` hits the early return and yields the record unchanged, so the derivation catches nothing and the guard is a no-op. The plan requires V-01 to paste this assertion's RED output as the non-vacuity proof (F-06), so an executor finds it green pre-fix and will most likely either conclude the defect is already fixed or delete the assertion as broken. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (use a non-empty `fields` list; demonstrated) | FIXED | E-01 now mandates a NON-EMPTY projection, names the early return as the reason, and cites the measurement; its Expected outcome states that a third assertion passing before the fix "has been written wrong, not satisfied". V-01 requires the `fields` argument QUOTED and confirmed non-empty. New F-12 carries both measurements. |
| PR-902 | HIGH | IN-SCOPE | E. Testing / D. Anti-regression | `validate_agent_record`'s `is_preview = outcome == "preview" or record.get("applied") is False`; review probe printing `outcome=preview ... catches: []` and `outcome=clean ... catches: ['applied']` on otherwise identical records | **THE DERIVATION CANNOT CATCH `applied` UNLESS THE CORPUS IS SHAPED FOR IT**, and the natural shape fails. On a `preview`-outcome record the greenwash exemption already holds via the outcome, so deleting `applied` leaves the record valid and the derivation reports nothing. A corpus built from the preview shape pins three of the four fields and silently leaves unpinned the one F-03 exists to protect, while V-01 would accept it because "at least the four fields" was the stated bar. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now requires the corpus to carry the `clean` + `complete: false` + `applied: false` shape and to assert all four names; its Expected outcome says ALL FOUR rather than "at least"; V-01 states that a derivation naming only three is a FAILED validation and gives the reason. Recorded in F-12. |
| PR-903 | HIGH | IN-SCOPE | D. Anti-regression / E. Testing | bare `python3 -m pytest` at review printing `3075 passed, 2 skipped, 3 warnings in 41.17s`; `tests/test_dependency_block_reporting.py -o addopts=""` printing `8 passed`; `git log --oneline -3 --` naming `f1b5b9ff`; `rg -n "dependencies"` showing `["executed:aaa111"]`; `03aicr` still `- Status: open` with `- Blocks-Release: next` | **THE BASELINE IS INVERTED AND THE CARRIER IS STALE.** F-09 instructs the executor to expect one failing test, to compare against `1 failed, 3034 passed`, and to treat a GREEN run as needing explanation. That test was fixed by `f1b5b9ff` using exactly the remedy `03aicr` proposed, and the suite is green. So the plan teaches an executor to accept a red suite and distrust a clean one. Separately, `03aicr` is still open and still release-gated, so a release is now gated on completed work. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-09 rewritten with both measurements and the repairing commit; the bar restated as ZERO failures against a baseline re-derived at lane start; the gate paragraph and V-04 corrected; the Deferred row rewritten to record a resolved condition. E-04 now requires `03aicr`'s staleness REPORTED and explicitly NOT closed (another party's item; a gated close has its own predicate), and requires `cm80ge`/`rcjorx` liveness confirmed BY SUBJECT rather than by status alone, which is what let `03aicr` go stale unnoticed. |
| PR-904 | MEDIUM | UNDER-SCOPE | C. Single source of truth | `filter_record_fields`'s docstring: "Project record fields down to requested set while preserving mandatory envelope fields"; plan E-02's "Change no other executable line"; V-02's "exactly one changed expression ... and NOTHING else" | **THE FUNCTION'S OWN DOCSTRING STATES THE SUPERSEDED CONTRACT AND THE PLAN NEVER UPDATES IT**, so after E-02 it becomes the THIRD stale statement beside the two documents E-03 fixes, and it is the one a developer reads first. Worse, V-02 as authored would REJECT a diff that fixed it, since it demanded the diff show nothing but the constant and one expression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires the docstring amended, noting it is a docstring and not an executable line so it does not conflict with the no-other-line rule. V-02's diff expectation widened to include it. |
| PR-905 | MEDIUM | IN-SCOPE | D. Anti-regression (live-artifact counts) | plan F-04's `30 invalid projections` of `53`; review sweep over an independent 10-record corpus printing `fix=False: 16 invalid projections of 41` and `fix=True: 0 invalid projections of 41`, `added=0 altered=0` in both | **F-04's TWO FIGURES ARE CORPUS-DEPENDENT BUT ARE STATED AS AN ACCEPTANCE BAR.** V-02 told the executor the pre-fix count "must be 0, against 30 pre-fix" and to report divergence from 30; a differently-shaped corpus of the same size measures 16 of 41, so the numerator, denominator and ratio all move. An executor re-running the sweep sees a mismatch and cannot tell whether the corpus differs or the plan was wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 now carries both measurements, labels the counts corpus-dependent, and states the INVARIANT as the direction (positive before, exactly zero after). V-02 restated accordingly, with the added instruction that a pre-fix count of ZERO means the sweep is not exercising the defect and is itself a stop condition. |
| PR-906 | MEDIUM | IN-SCOPE | A. Correctness / G. Plan executability | `rg -n "filter_record_fields" agent_workflows/` returning four call sites; the fourth in `run_analytics_cli`'s refused-query branch hand-building an `error` record under `if ctx.fields:` | **F-10 UNDERCOUNTS THE CALL SITES (three claimed, four exist)**, and E-02's safety claim rests on EVERY site guarding on a truthy `fields`. A site the plan does not know about is a site it has not checked. Verified harmless here (an `error` record's required fields are all inside the seven-field envelope, so that projection is safe today and stays safe), so this is an incomplete survey rather than a second defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 corrected to name all four sites, record the fourth's guard and record kind, and state explicitly why it is not a second instance of the defect. |
| PR-907 | LOW | IN-SCOPE | Evidence accuracy | `rg -c "_MANDATORY_FIELDS" agent_workflows/*.py` returning `agent_schema.py:2` and `run_analytics_cli.py:1` | F-02 CLAIMS "exactly two references in the package"; there are three. The third is the `run_analytics_cli` comment that names the constant in prose, which is precisely the reference E-02's do-not-widen-in-place instruction exists to protect, so the undercount contradicts the plan's own reasoning two sections later. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02's evidence cell corrected to three references, naming the third and why it matters to E-02. |
| PR-908 | LOW | IN-SCOPE | A. Correctness (completeness of the fix) | Review extraction over `inspect.getsource(validate_agent_record)` printing eleven consulted names and `NOT covered: []` against E-02's union; probe of two adversarial records printing `narrow valid: True` beside `wide valid: True` for both | THE PLAN CLAIMS ONLY SUFFICIENCY-ON-A-CORPUS WHERE COMPLETENESS IS PROVABLE AND CHEAP, and it never checks the reverse risk that retaining MORE fields could invalidate a record (the summary count-consistency rule is exactly that shape). Both gaps are favourable once measured, so this strengthens the plan rather than changing the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-13 (eleven consulted names, all covered, so the fix is complete by construction at this HEAD and E-01's guard exists to catch a twelfth) and F-14 (the wide set breaks neither adversarial record, because the count rule fires only on `kind == "summary"`). V-02 now requires the extracted-name list pasted beside the constant as a completeness proof. OQ-02 upgraded from sufficient to complete. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01's derived property is vacuous as specified. Fix the projection argument, or replace the derivation with something else? | FIX THE ARGUMENT to a non-empty `fields` list and CONSTRAIN THE CORPUS so `applied` is reachable; keep the derivation. | (a) Replace the derivation with an explicit four-name assertion - REJECTED: F-06 argues correctly that a literal list restates the same set a third time and drifts the same way, which is the defect being fixed; the derivation's whole value is catching a TWELFTH field nobody has thought of. (b) Strengthen it to an exhaustive subset sweep in the committed test - REJECTED as unnecessary at this HEAD: review probed for a requirement that only a COMBINATION of deletions triggers and found none on either kind, so single-field deletion is equivalent here and far cheaper; the one-time exhaustive sweep already required by V-02 covers the combination case at execution. | `filter_record_fields`'s `if not fields: return dict(record)`; the `fields=[]` versus `fields=['cmd']` derivations; the `is_preview` expression and the `preview` versus `clean` derivations; the combination-requirement probe returning none | yes |
| D-2 | The authored suite baseline names a failure that is fixed, and its carrier is still release-gated. Update the numbers, close the carrier, or report it? | RESTATE THE BAR as zero failures re-derived at lane start, and REPORT the stale carrier without closing it. | (a) Close `03aicr` as part of this plan - REJECTED: it is another party's item, closing a `Blocks-Release` item runs a gated predicate requiring handoff, evidence or de-gating, and a release gate should be cleared by a deliberate human act rather than as a side effect of an unrelated fix. (b) Substitute the review figure `3075 passed` as the new bar - REJECTED: the count moves with every merge (this lane already saw 3069 then 3075 within hours), so a fresh fixed figure expires the same way; the live-artifact convention says a drifting count is context, never the bar. (c) Say nothing, since a green suite is good news - REJECTED: a still-open release-gated item for completed work is a real defect in the release view, and silence is how it stays. | bare suite green at review; `f1b5b9ff`; the synthetic `executed:aaa111` token; `03aicr`'s own suggested remedy matching what landed; `03aicr` front matter still `open` + `Blocks-Release: next`; the AGENTS.md close-legitimacy rule for a gated item | yes |
| D-3 | F-04's counts do not reproduce on a different corpus. Re-measure and substitute, or change what is asserted? | ASSERT THE DIRECTION (positive before, zero after) and keep both measurements as context. | (a) Substitute the review figures (16 of 41) - REJECTED: they are no more canonical than the authored ones, since both are artifacts of an arbitrary corpus, so substituting would just move the expiry date. (b) Drop the sweep - REJECTED: it is the evidence that the fix generalizes beyond the two known instances, and F-04 is the argument for fixing the projector rather than a caller. | the two sweeps' printed counts over different corpora; the live-artifact re-derivation convention | yes |
| D-4 | `filter_record_fields`'s docstring states the old contract, but E-02 forbids other line changes and V-02 forbids other diff content. Amend it here, or carry it? | AMEND IT IN E-02. | (a) Carry it to a follow-up item - REJECTED: the drift would be CREATED by this plan, in the very function it changes, and it is the same defect class (a statement of the preserved set going stale) that E-03 exists to fix in two documents; deferring one line of the three is indefensible. (b) Leave the docstring and let the documents carry the truth - REJECTED: a developer reading the function reads the docstring, not `docs/cli-output-contract.md`, so this is the highest-traffic of the three statements. | the docstring's current text; E-02's no-other-executable-line rule (a docstring is not executable); E-03's scope covering the two documents but not this | yes |

### Deferred and open

None. Every finding is FIXED, including the BLOCKER (PR-901). No finding was left OPEN or DEFERRED, so
no escalation to a `- Blocking: yes` open question is owed under the repository's `HIGH` gate threshold.
The plan's two open questions were already `resolved` and remain so: OQ-01's choice of fix (a) over (b)
was re-verified (F-03 reproduced end to end, which is the measurement it rests on) and stands unchanged,
and OQ-02's flat-union choice was STRENGTHENED from sufficient-on-a-corpus to complete-by-construction
(F-13) with the reverse risk probed (F-14). The three carriers were checked: `cm80ge` and `rcjorx` are
live and their subjects verified directly (the stale comment is still in `run_analytics_cli`; `aw find
plans --agent --fields findings` still exits `unrecognized arguments: --fields`), while `03aicr` is
STALE and deliberately left alone with the divergence carried into E-04. No decision above carries
`Reversible: no`.

ONE ADVISORY IS KNOWINGLY LEFT STANDING. `aw ipd lint` reports one `IPD-Z602` density advisory on E-01,
which is pre-existing (it fired on the authored text too, alongside a second on E-04 that this revision
cleared). It was assessed on the rubric's right-sizing diagnostics rather than deferred to the count:
E-01 produces ONE deliverable, a single new test file, verified by ONE V-item, and its four assertions
are four facets of one contract that share a corpus and would be meaningless apart. Splitting it would
create files that cannot be validated independently. The advisory is firing on clause count in prose
that is load-bearing (it is what stops the two vacuity traps PR-901 and PR-902 identified), so
shortening it to satisfy a regex would trade real executability guidance for a clean lint line.

FINAL GATES: `aw ipd lint --phase author --agent` exit 0 before revision (2 advisories);
`--phase review-finalize --agent` exit 0 after (1 advisory, E-01, pre-existing); `aw check` unchanged at
its pre-existing findings with none on this plan; bare `python3 -m pytest` -> `3075 passed, 2 skipped,
3 warnings in 41.17s`; four live `--agent --fields findings` runs each emitting a valid record;
`aw sanitize --agent` clean; `git status --porcelain` showing exactly the plan (modified) and this
record (new).
