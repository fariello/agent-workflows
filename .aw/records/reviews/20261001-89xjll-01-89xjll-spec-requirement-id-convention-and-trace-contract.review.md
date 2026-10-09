# Review findings: spec 89xjll

- Subject-Id: 89xjll
- Subject-Type: spec
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `81cb4f85` in a non-interactive review-sweep lane. Structural preflight `aw specs check`
CONFORMED (exit 0) before semantic review and again after revisions. The spec was already committed and
unchanged, so no pre-review snapshot was needed. `aw ipd lint` was never invoked against the spec; no
`- Readiness:` was added; status and history were left to `aw specs set` / `aw specs note`.

RE-MEASURED: `_SPEC_ACTIONS` maps only `approved` to `ACTION_PLAN` (`agent_workflows/run_selection_policy.py`
`_SPEC_ACTIONS`); the three sibling verifiers and their signatures (`production_checks.spec_plan_count`,
`spec_plan_conformance`, `spec_plan_gate_carry`); `new_produced_paths` / `baseline_plan_ids` at the SPEC
production block of `runner_shared.py`; `config.KNOWN_FEATURE_CUTOVERS` and `resolve_cutover_date`'s
fail-open tier 3; `check_engine._spec_requires_id6` filename comparand; `[Must]` in exactly 2 of 12 approved
specs; 12 approved specs with the stated id families; `25kzda` 4.8's TRACE row; `z7nbn1` 4.4's deferral
text; `vkub9o` Sections 3.2, 3.3, 5 and Q5. Census totals moved from 39 to 40 only by this spec's arrival.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | HIGH | IN-SCOPE | A (claims current), G | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md:969` row `SPEC-PLAN-TRACE` | The spec claims to adopt `25kzda` 4.8 VERBATIM but misquoted both the pass criterion (split "and" into ";", added a period) and the message template ("Re-read spec <source-id> and update plan checklist, then: aw <host> run <selector>" versus the real "Correct and sync the IPD, then: aw <host> run resume <run-id>"). An implementer following this spec would ship a template that contradicts the row it adopts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Sections 1 and 6.2 now quote the row exactly; correction noted in 6.2. Decision to adopt verbatim unchanged. |
| SR-002 | HIGH | UNDER-SCOPE | B, C, G | `25kzda` 4.8 TRACE row, third conjunct "there are no unknown references"; spec draft 6.2/6.4 | The adopted pass criterion's third conjunct (reverse direction: plan cites an id the spec does not declare) was quoted but never specified: no behavior, no acceptance criterion, and no rule for distinguishing a citation of the producing spec from a mention of another spec's id. The implementing plan `rtvdak` E-05 had to invent it. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | OPEN | New 6.2a states the conjunct is in scope and its message shape; the attribution rule is a design choice with real options and is raised as OQ-05 (blocking, owner maintainer). AC-5 now covers the unknown-reference failure per the OQ-05 ruling. |
| SR-003 | HIGH | IN-SCOPE | B, D | spec 3.1 FORM C; OQ-01 A + OQ-03 A; `2vev8j` `- N1 NOT a rewrite` under `## 3a. Non-goals` versus `2lcqno` `- **N1 (setid is ...)**` under `## 3. The normative model`; `25kzda:177-180` `\| A1:` rows in `### 1.4 Resolution of the required revisions` | Combining "all declared ids mandatory" with "FORM C numbered headings are requirement handles" makes every numbered heading of a post-cutover spec (including "Why this exists") a mandatory requirement, makes revision-resolution `A1:` rows acceptance criteria, and makes an `N`-prefixed non-goal mandatory. The rule is section-blind. This spec would itself fail its own rule. Choosing among fixes narrows OQ-03's recorded recommendation, so it is the maintainer's call. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | OPEN | Raised as OQ-04 (blocking, owner maintainer) with three options and a reviewer recommendation (FORM A only, excluding `N`). 3.1 now separates "valid addressing handle" from "TRACE-mandatory" and forbids implementing Section 6 until OQ-04 is ratified. |
| SR-004 | MEDIUM | UNDER-SCOPE | G | `ipd_lint._ORCH_ROW_RE`; plan `rtvdak` resolved OQ (orchestrator rows); `25kzda` 4.8 `SPEC-PLAN-COUNT` "At least one new IPD links to the spec" | The spec did not say whether coverage is per plan or across the produced plan set. Per-plan would fail every produced Set with an orchestrator. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 6.1 now specifies set-level coverage and that orchestrator child-tracking rows contribute nothing; leaves the cited-text surface to the plan, which must state and test it. Recorded as D-1. |
| SR-005 | MEDIUM | IN-SCOPE | C | draft Section 9 AC-1..AC-5 | Acceptance criteria asserted properties of the document ("the specification defines ...") rather than observable behavior of the shipped check, mapped to no requirement ids, and covered no failure or refusal path. The spec's own requirements had no stable ids although the spec is the id convention. Also OQ-01's optional marker was unspecified ("e.g."). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Section 1b requirement index R-1..R-7; rewrote Section 9 as AC-1..AC-8 table mapping to R-ids with evidence, including failure, grandfathered, vacuous, and no-regression paths. OQ-01 marker grammar made exact (`[Should]`/`[Optional]`, the only markers in the corpus). Recorded as D-2. |
| SR-006 | MEDIUM | IN-SCOPE | A | `25kzda:177-180`; grep of approved specs | Stale or wrong counts: "7 of 12 approved carry acceptance IDs" counted `25kzda`'s revision-resolution rows as acceptance criteria (true figure 6, with 2 lacking an acceptance heading); "would invalidate 5 of the 10" named only 3 specs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 2 and 3.1 corrected with the measured figures and the N-semantics divergence recorded. |
| SR-007 | MEDIUM | IN-SCOPE | D, F | `agent_workflows/config.py` `resolve_cutover_date` tier 3 `None`; `agent_workflows/check_engine.py` `PROMPT_ID6_CUTOVER_DATE` comment; `check_engine._spec_requires_id6` | 5.1 said the boundary is "not hardcoded into source logic" and compared against "front matter or filename" date. Precedent requires a non-`None` module fallback (else decoration mode in fresh clones/CI), and every shipped cutover uses the filename date only; two comparands is ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 5.1 now requires the fallback constant and fixes the comparand to the filename date, with the accepted consequence. Matches `rtvdak` E-06. |
| SR-008 | MEDIUM | UNDER-SCOPE | F | `vkub9o` Section 5 item 3; draft Sections 1, 6.4, 7 | No Non-goals section; the spec departs from `vkub9o`'s explicit "Do NOT build a requirement parser" without saying so; and the honest limits omitted that TRACE passes VACUOUSLY on all 12 current approved specs (all pre-cutover), yet a vacuous pass could be described as trace-verified. 6.4 also claimed to "replace" `z7nbn1` 4.4 now, contradicting Section 7. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Section 1a Non-goals; Section 1 states the departure and its basis (maintainer ruling in `vy20et`); 6.3/6.4 state the vacuous-pass limit and forbid calling it trace-verified; 6.4 aligned with Section 7. |
| SR-009 | LOW | IN-SCOPE | A | `vkub9o` 3.3 (`runner_shared.py:6636` is `return run_recovery.validate_retry_budget(cli_value)`) | 4.2 cited `runner_shared.py:6636` as a comment citing §2.1; it is a code call, and the comment in question is elsewhere. `xipfy1` described as pending is executed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 4.2 and Section 1 reworded to cite `vkub9o` 3.3 directly. |
| SR-010 | LOW | IN-SCOPE | G | spec Section 7; `vy20et` front matter | Dependencies on `rtvdak` and `vy20et` lacked direction and gate status. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 7 names `rtvdak` (depends on this spec) and states `vy20et` carries no `Blocks-Release`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | Is TRACE coverage evaluated per produced plan or across the produced set? | Across the set; orchestrator child-tracking rows contribute nothing. | Per plan, rejected: fails every Set with an orchestrator for a reason unrelated to coverage. | `ipd_lint._ORCH_ROW_RE`; `25kzda` 4.8 `SPEC-PLAN-COUNT` set-level reading; plan `rtvdak` resolved OQ | yes - nothing ships until `rtvdak` executes |
| D-2 | What exactly marks a requirement non-mandatory under OQ-01 Option A? | `[Should]` or `[Optional]` immediately after the id at its declaration site; no optional form for acceptance criteria. | Leave as "e.g.", rejected: not implementable; `(optional)` in prose, rejected: indistinguishable from mention text. | corpus grep: `[Should]` 5, `[Optional]` 0 outside this spec, `[Must]` 8 | yes - spec is pre-approval |
| D-3 | Should the template misquote be fixed or treated as a deliberate amendment? | Fix to the verbatim row. | Treat as amendment, rejected: OQ-02 explicitly decides ADOPT verbatim and the spec states no amendment. | `25kzda:969`; spec OQ-02 | yes |

### Verdict

`REVIEWED - OPEN QUESTIONS`. Ten findings: eight FIXED in place, two HIGH findings (SR-002, SR-003) left
OPEN because each needs a maintainer design choice; both are raised in the spec as blocking OQ-05 and OQ-04
naming the finding ids. Not ready for human approval until OQ-04 and OQ-05 are ruled and a re-review round
records them. This record GATES approval at the HIGH threshold by design.

## Round 2

Re-review requested 2026-10-08 after the maintainer resolved OQ-04..OQ-07 (/askme) and the spec body was
amended to match (commit `1c4352876`). Interactive run: one new decision (OQ-08) was asked and answered.
Structural preflight `aw specs check` CONFORMED before and after revisions. `aw ipd lint` was not invoked;
no `- Readiness:` was written; status and history were left to `aw specs set` / `aw specs note`.

RE-MEASURED: `production_checks._TERMINAL_DISPOSITIONS` (`agent_workflows/production_checks.py:29`) and
`existing_handoff_plans` skip `executed`; the spec production block pools `existing_linked_plans` with
`new_produced_plans` as `all_verified_plans` and passes it to `spec_plan_set`/`spec_plan_conformance`/
`spec_plan_gate_carry` (`agent_workflows/runner_shared.py`, spec production block); a passing production
runs `specs set --status implementing` (`runner_shared.commit_spec_transition_output`);
`run_selection_policy._SPEC_ACTIONS` maps only `approved` to `ACTION_PLAN` and `implementing` to child
dispatch (`agent_workflows/run_selection_policy.py:151-163`); `attention_contract` allows
`implementing -> approved` and `->approved` requires the human attestation; the spec setter has two
spellings (`agent_workflows/specs.py` fork and `status_set.run_set_command`); `[Deferred]` appears in no
other spec; every R-* maps to an AC-* and every AC-* back to an R-*.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-002 | HIGH | UNDER-SCOPE | B, C, G | spec 6.2a, new 6.2b; OQ-05 resolved | The unknown-reference conjunct's attribution rule is now specified: only citations qualified with the producing spec's id6 count, in all three conjuncts, with the measured basis (160 unqualified non-declared tokens in 44 of 116 From-Spec plans). AC-5 covers the qualified-unknown failure and the unqualified-ignored case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer ruling OQ-05 (B), applied in 6.2b, R-5, AC-4, AC-5. |
| SR-003 | HIGH | IN-SCOPE | B, D | spec 3.1, 1b R-1; OQ-04 resolved | TRACE-mandatory forms are now decided: FORM A only, excluding `N`; FORM B/C are addressing handles never extracted. The spec's own 22 numbered headings no longer become requirements. AC-1 asserts FORM B, FORM C and `N` ids are not returned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer ruling OQ-04 (A + N exclusion), applied in 3.1, R-1, AC-1; OQ-03 annotated as narrowed. |
| SR-011 | MEDIUM | IN-SCOPE | A, G | `agent_workflows/production_checks.py:29` `_TERMINAL_DISPOSITIONS = frozenset(("executed", "superseded", "not-executed"))` | The amended 6.1 claimed `existing_handoff_plans` returns `executed` plans; it skips them. A pooled set built on it would drop an executed first-stage plan and make a later stage re-cover finished work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 6.1 now states TRACE's pooled set is the runner's set PLUS executed linked plans; superseded/not-executed excluded; sibling checks unchanged. AC-4 asserts an executed linked plan contributes coverage. |
| SR-012 | HIGH | UNDER-SCOPE | G | `runner_shared.commit_spec_transition_output`; `run_selection_policy._SPEC_ACTIONS`; spec 3.3 | Staged planning (OQ-07) had no way to start a second stage: a passing production moves the spec to `implementing`, and only `approved` specs get a plan-writing turn. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Asked the maintainer (OQ-08): stay `implementing`; target design is a runner plan-writing turn for an `implementing` spec with uncited non-deferred ids, delivered separately with a `25kzda` amendment (backlog `2wkzf7`); stopgap is a human-attested `implementing -> approved` step. Recorded in 3.3 and Section 7. |
| SR-013 | MEDIUM | IN-SCOPE | C, G | spec 7 (rtvdak note); `rtvdak` `- Status: approved` | The implementing plan `rtvdak` is approved against the superseded contract (R-1..R-7, new-plans-only coverage, unqualified citations, no markers); R-9 also touches the spec status setter, likely outside its scope. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Section 7 states `rtvdak` MUST be re-reviewed against this spec before it executes. Moving `rtvdak` back to `to-review` is a plan action outside this review's remit and is reported to the maintainer. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-4 | Should TRACE's pooled set include `executed` linked plans? | Yes; superseded and not-executed excluded. | Reuse `existing_handoff_plans` unchanged (drops executed), rejected: a later stage would have to re-cite finished work, defeating OQ-06. | `production_checks.py:29`; OQ-06 intent (pool all linked plans) | yes - nothing ships until `rtvdak` executes |

### Verdict

`APPROVE WITH REVISIONS APPLIED`. SR-002 and SR-003 are FIXED on the maintainer's rulings (OQ-05, OQ-04);
three new findings (SR-011, SR-012, SR-013) were fixed in place, SR-012 after one interactive decision
(OQ-08). No finding remains open at or above the gate threshold. Ready for the human approval gate.
Before approval the maintainer should know: `rtvdak` must be re-reviewed before executing, and staging a
spec relies on the step-back stopgap until backlog `2wkzf7` ships.
