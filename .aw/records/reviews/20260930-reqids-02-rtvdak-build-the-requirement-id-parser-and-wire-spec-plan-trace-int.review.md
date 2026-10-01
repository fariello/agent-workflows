# Review findings: plan rtvdak

- Subject-Id: rtvdak
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
reports `clean` again at `author` and `review-finalize` after revision. The plan is `- Kind: child`, so
the `IPD-S407` orchestrator child-row check does not apply.

EVERY ONE OF THE PLAN'S TEN AUTHORED FINDINGS REPRODUCES, AND THE DESIGN IS RIGHT. F-01: `grep -rn
'SPEC-PLAN-TRACE' agent_workflows/` is still empty (exit 1) while `production_checks.py` implements the
three siblings and its module docstring names exactly those three as in scope "from spec 25kzda 4.8 /
z7nbn1 4.4". F-02 is the plan's hinge and it holds by reading the code: the SPEC production block
computes `new_produced_paths` by diffing `_ce._iter_plan_ipds(target_tree)` against `baseline_plan_ids`
and passes that list into `spec_plan_conformance` and `spec_plan_gate_carry`, so research `vkub9o`'s
decisive objection (0 plans carrying a `From-Spec` edge) genuinely does not reach a check running inside
the dispatcher that just computed the set. F-03: `run_selection_policy._SPEC_ACTIONS` maps ONLY
`approved` to `ACTION_PLAN`, with `implemented`/`deferred`/`parked`/`superseded` to `ACTION_SKIP` and
`draft`/`to-review`/`reviewed`/`implementing` deliberately absent. F-05: `[Must]` appears in exactly 2 of
the 12 approved specs (`5tapom`, `2vev8j`), so the marker-based mandatory reading really is measurably
vacuous on the judged population. F-06: `ipd_lint.Leaf` still carries `kind`, `ident`, `checked`, `text`,
`line`, `section`, `fields`, `target` and `ParsedDoc` still carries `exec_leaves`/`valid_leaves`. F-07's
quoted registry comment and both precedent entries read as quoted. F-10's correction (that a
`state:spec:approved:` edge CAN express the approval dependency) is right, and Order 01's E-09 already
owns writing it, reviewed yesterday. `25kzda` 4.8's TRACE row, its `RETRY, then FAIL ITEM` Action and its
message template match the plan's quotation verbatim, and `z7nbn1` 4.4's deferral language including "a
produced plan MUST NOT be described as trace-verified" reads exactly as quoted. OQ-02's reasoning is
correct and well-grounded: `ipd_lint._ORCH_ROW_RE` is `^- \[[ x]\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6})
REACHED ([A-Za-z][A-Za-z-]*)$`, so an orchestrator's rows cite no requirement by construction and the
set-level reading is the only workable one.

BUT THE PLAN IMPLEMENTS TWO THIRDS OF THE CONTRACT IT CLAIMS TO RENDER. That is PR-001 and it is the
dominant finding. `25kzda` 4.8's pass criterion is three conjuncts: "Every mandatory spec requirement
maps to at least one E item and every acceptance criterion maps to at least one V item; **there are no
unknown references**". The plan quotes the first two in E-05, V-05, the Goal and the approval gate, and
the string "unknown reference" appears NOWHERE in the plan (measured: zero matches). The dropped conjunct
is the REVERSE direction, and it is the half that catches the likeliest real error: a plan citing `R-99`
where the spec declares no `R-99` is a typo or a stale citation, which a forward-only coverage check
cannot see. Shipping it silently would mean the verifier renders `25kzda` 4.8's message, quotes its pass
criterion in its docstring as the three siblings do, and implements two of its three clauses, which is
the specific kind of overclaim this repository's honest-documentation principle exists to stop. The fix
is cheap, which is part of why omitting it is not acceptable: E-03 already returns the declared sets, so
an unknown reference is just a plan-side id absent from them. I required a decision rather than
mandating implementation, because E-01 may find Order 01's approved spec rules on it, and I named the one
real hazard (a plan legitimately cites OTHER specs' ids in prose, so an all-text scan would fire
constantly) so it is handled rather than discovered.

FOUR MEASUREMENT CORRECTIONS, each found by driving the code rather than reading it. PR-002: `Leaf.text`
is ONLY the item's first-line remainder. Driving `ipd_lint.parse` on this very plan, `exec_leaves[0].text`
ends mid-sentence while `exec_leaves[0].fields` holds `['Depends on', 'Expected outcome', 'Execution
state']`. So "each produced plan's `E-*`/`V-*` item text" names two different possible surfaces, and a
requirement cited in an `Expected outcome` sub-field would read as uncovered. That is a defensible
choice but not a defensible accident. The same item also carries PR-002's second half: the three sibling
signatures are NOT uniform, and the plan's instruction to "match the sibling signature" is ambiguous on
the one argument that matters. Measured, `spec_plan_count` and `spec_plan_gate_carry` take no `run_id`;
only `spec_plan_conformance` does. TRACE's message template contains `<run-id>`, so TRACE must copy
`spec_plan_conformance` specifically. I also flagged that the function contains a near-identical BACKLOG
production block (`backlog_graduate_count`/`backlog_graduate_ipd`/`backlog_gate_handoff` over its own
`new_produced_paths`), because the two clusters look alike and wiring a spec check into the backlog path
would be a silent error.

PR-003 is the one I expect to be least obvious and most consequential. The plan's F-07 correctly quotes
the registry comment and correctly identifies the decoration failure mode, then E-06 implements only half
the precedent it cites. Each of the three precedent features ships a non-`None` MODULE CONSTANT beside
the registry entry, and `check_engine` states the reason in terms that apply here unchanged: "a
config-only resolver fails open to `None` and grandfathers every prompt forever ... while a constant-only
rule ships an immovable date in a repo that already moved that capability into config". Measured,
`resolve_cutover_date` tier 2 reads `installs.jsonl`, which a fresh clone or CI checkout need not carry,
so E-06's own expected outcome ("returns a non-`None` boundary IN THIS REPOSITORY") is satisfiable while
the check still ships as decoration everywhere else, which is exactly the defect F-07 says the item
exists to prevent. I also required the COMPARAND be stated, because the plan never says what the date is
compared against: every shipped cutover compares the artifact's FILENAME date, and copying that is right.

PR-004: two of E-04's five named corpus shapes were wrong, and the real variety is wider than F-04
records. `6m4kow` does NOT use an `AC-` prefix, it uses `- **A-01**`; no `AC-` form appears in any
approved spec at all. `7ckptx` uses `- A1.` and `w15vzb` uses `- **A-1**`. So at least three distinct
acceptance shapes exist across the approved corpus, and a test written to the plan's description would
have asserted a premise the file does not satisfy. This WIDENS the obligation rather than narrowing it,
and it strengthens the plan's own case: the more shapes there are, the more the convention is needed.

PR-005: the pinned baseline `3387 passed, 2 skipped` at HEAD `764442f7` is stale. Measured bare in this
lane: `3531 passed, 2 skipped, 3 warnings in 76.16s`, a drift of 144 tests. Worth noting in the plan's
favour, the suite is GREEN here, so the one pre-existing failure Order 01's review recorded against
backlog `fnb8pl` has since cleared. The plan already said the baseline is re-established at execution,
which is correct practice; what I fixed is that it also wrote the number as if it were a bar. The
repository's own statement of the right rule is in spec `6m4kow` A-03 ("A criterion phrased as equality
against a count would fail for a reason unrelated to the change"), which this plan's V-08 should follow.

WHAT I DID NOT FLAG, recorded so it is not re-litigated. The plan's refusal to declare any `.spec.md` is
correct and well-argued (F-08 measures five pending plans already queuing `25kzda` edits, so a silent
sixth is exactly what must not happen). Its five Carrier-Declined deferral rows are honest: each declines
with a reason grounded in `vkub9o`'s costed options or in settled policy, not parked work. The decision
to place the parser in `production_checks.py` rather than `specs.py` is sound, since no requirement-id
parser exists anywhere in the package today (searched) and the only consumer is this verifier. OQ-01 and
OQ-02 are both `Blocking: no` with resolutions I checked and agree with, so I left both as the author
wrote them; OQ-01 in particular correctly refuses to pre-empt a maintainer decision that Order 01's spec
approval settles, and correctly records the consequence if the marker reading was ratified. The
self-named "sharpest question" paragraph in the gate (that `vkub9o` recommends against building a parser)
is the right way to surface a reviewer-level objection, and its reconciliation via F-02 holds on
measurement.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A (correctness) / F (honest documentation) | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md:964`, TRACE row pass criterion "Every mandatory spec requirement maps to at least one E item and every acceptance criterion maps to at least one V item; there are no unknown references"; measured zero matches for "unknown reference" anywhere in the plan | **THE PASS CRITERION HAS THREE CONJUNCTS AND THE PLAN IMPLEMENTS TWO, WHILE THE CODE WOULD RENDER THE ROW'S MESSAGE AND QUOTE ITS CRITERION.** The dropped clause is the reverse-direction check (a plan citing an id the spec does not declare), which is what catches a typo or a stale citation; a forward-only coverage check is blind to it. Shipping two of three silently claims the row and does not implement it, and leaves `z7nbn1` 4.4's deferral only partly discharged while the plan asserts it is closed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires a RECORDED disposition: implement it (preferred; E-03 already returns the declared sets, so an unknown reference is a plan-side id absent from them, and the template's `<ids>` field carries it) or defer it with a carrier plus an explicit statement that TRACE ships two of three conjuncts and `z7nbn1` 4.4 is only partly discharged. The one real hazard is named (a plan legitimately cites other specs' ids in prose, so the rule must be scoped to citations of THIS spec) and E-08 must prove that negative. V-05 demands the disposition and the driven cases; the Goal and the approval gate are swept to match. New F-11. |
| PR-002 | MEDIUM | IN-SCOPE | A / G (executability) | Driven `ipd_lint.parse` on this plan: `exec_leaves[0].text` is the first-line remainder, `exec_leaves[0].fields` is `['Depends on', 'Expected outcome', 'Execution state']`; `production_checks.spec_plan_count(repo, spec_id6, baseline_plan_ids, *, host)` and `spec_plan_gate_carry(repo, spec_id6, produced_paths, *, host)` versus `spec_plan_conformance(repo, spec_id6, produced_paths, *, host, run_id)` | **TWO UNDERSPECIFICATIONS THAT BOTH DECIDE REAL BEHAVIOR.** "Read the item text" names two possible surfaces, and reading `text` alone silently misses a citation written in an `Expected outcome` sub-field, producing a false refusal. Separately, "match the sibling signature" is ambiguous because the three siblings differ on exactly the argument TRACE's template needs: only `spec_plan_conformance` takes `run_id`, and TRACE's message contains `<run-id>`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires the three signatures recorded INDIVIDUALLY with `spec_plan_conformance` named as the shape to copy, plus a driven demonstration of `text` versus `fields` and a STATED decision on which surface is searched with its consequence. E-05 implements that choice deliberately and E-08 pins it. E-07 names `spec_plan_conformance`'s argument list and flags the near-identical BACKLOG block so the right cluster is edited. V-02 and V-05 updated. New F-12, F-13. |
| PR-003 | MEDIUM | UNDER-SCOPE | C (operability) / D (anti-regression) | `agent_workflows/check_engine.py:69-79` ("The fallback is non-`None` DELIBERATELY, which is what avoids BOTH documented failure modes: a config-only resolver fails open to `None` and grandfathers every prompt forever ... while a constant-only rule ships an immovable date"), `PROMPT_ID6_CUTOVER_DATE = "20260921"`, `WALKTHROUGH_ID6_CUTOVER_DATE = "20260927"`; `agent_workflows/config.py:1334` `_find_install_history_cutover` reading `installs.jsonl` | **REGISTERING THE KEY ALONE SHIPS THE DECORATION MODE THE PLAN'S OWN F-07 EXISTS TO PREVENT.** Every precedent feature ships a non-`None` module fallback BESIDE the registry entry, for the reason `check_engine` states. `resolve_cutover_date` tier 2 depends on `installs.jsonl`, absent in a fresh clone or CI checkout, so E-06's expected outcome (non-`None` IN THIS REPOSITORY) is satisfiable while grandfathering everything forever everywhere else. The plan also never states WHAT DATUM the cutover is compared against, without which grandfathering cannot be implemented at all. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-06 now requires the non-`None` module fallback constant with the two failure modes named in its comment, and requires the comparand stated as the spec's FILENAME date, matching every shipped cutover, with the grandfathering consequence recorded. V-06 requires the fallback demonstrated REACHED in a temp repo with no config key and no install history, proving the check is not decoration in a fresh clone. New F-14. |
| PR-004 | MEDIUM | IN-SCOPE | E (testing) / D | Measured: `6m4kow` uses `- **A-01**` (not `AC-`; no `AC-` form in any approved spec); `7ckptx` uses `- A1.`; `w15vzb` uses `- **A-1**` | **TWO OF E-04's FIVE NAMED CORPUS SHAPES ARE WRONG, so a test written to the plan's prose would assert a premise the file does not satisfy.** The plan attributes an `AC-` prefix to `6m4kow`, which that spec does not use, and F-04 implies two acceptance shapes where at least three exist. Since E-04's whole purpose is testing against REAL corpus variety rather than invented shapes, a wrong shape defeats the item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires every named shape RE-MEASURED from the file rather than taken from this plan's prose, covers all three observed acceptance shapes (`A1`, `A-1`, `A-01`), and requires that a non-conforming legacy shape yield an EMPTY declared-acceptance set rather than a partial one so the no-ids PASS case catches it. V-04 requires the re-measured shape of each named spec pasted. New F-15. |
| PR-005 | LOW | IN-SCOPE | E / F | Plan's `Required tests / validation` pinning `3387 passed, 2 skipped` at HEAD `764442f7`; measured bare in this lane `3531 passed, 2 skipped, 3 warnings in 76.16s`; spec `6m4kow` A-03 "A criterion phrased as equality against a count would fail for a reason unrelated to the change" | **THE PINNED BASELINE IS STALE BY 144 TESTS AND IS WRITTEN AS IF IT WERE A BAR.** The plan correctly says the baseline is re-established at execution, then also writes a count the executor could compare against. The repository has an explicit statement of the right rule in an approved spec, which this plan should follow. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The validation section now states the bar as the EMPTY failing-node-ID DELTA against a baseline measured in the executor's own lane, never equality with a count, citing `6m4kow` A-03; both the authoring and review numbers are retained explicitly as drift CONTEXT. V-08 forbids comparing against either. New F-16 also records that the suite is green here, so the pre-existing failure Order 01's review noted has cleared. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The pass criterion's third conjunct ("no unknown references") is unimplemented and unmentioned. Mandate it, or allow a deferral? | Require a RECORDED disposition: implement (preferred and the default) or defer with a carrier plus an explicit partial-discharge statement. | (a) Mandate implementation outright: REJECTED, E-01 reads the ratified convention off Order 01's approved spec and that spec could legitimately scope the namespace in a way that changes what an "unknown reference" is, so pre-committing the implementation here would have this plan decide something it has correctly delegated. (b) Leave it unmentioned: REJECTED, that is the defect; the code would render the row's message and quote its criterion while implementing two thirds of it. (c) Treat the omission as out of scope because the plan never claimed the third clause: REJECTED, the plan claims to close `z7nbn1` 4.4's deferral of TRACE, and TRACE is the whole row. | `25kzda` 4.8's TRACE row read in full; the plan's own E-05 instruction to render that row's template and quote its pass criterion as the three siblings do; `z7nbn1` 4.4's "MUST NOT be described as trace-verified" language that this plan discharges. | yes |
| D-2 | Which plan-item surface should the check search, given `text` and `fields` are separate? | Do NOT decide it here; require E-02 to RECORD the decision with its consequence and E-08 to pin it. | Mandating `text` alone: REJECTED as a reviewer substituting an implementation choice the executor is better placed to make once E-01's convention is known, though it is the narrowest and most likely right answer. Mandating `text` plus `fields`: REJECTED, it would make a citation in `Execution state` count, which is meaningless. Leaving it unstated as authored: REJECTED, it is the difference between a working check and a false-refusal generator, and it would be settled silently by whichever attribute the implementer happened to read. | Driven `ipd_lint.parse` output showing `text` is the first-line remainder and `fields` carries the sub-fields; the plan's own instruction to reuse `ipd_lint` rather than fork a parser. | yes |
| D-3 | Should E-06 ship a module fallback constant, which the plan did not ask for? | Yes, required. | Registry entry alone, as authored: REJECTED on the precedent the plan itself cites; `resolve_cutover_date` falls through to `None` without install history, so the check would be decoration in a fresh clone or CI while passing E-06's own stated outcome in this repository. Constant alone: REJECTED for the second failure mode `check_engine` names, an immovable date in a repo that moved the capability into config. | `check_engine`'s comment stating both failure modes verbatim; `PROMPT_ID6_CUTOVER_DATE` and `WALKTHROUGH_ID6_CUTOVER_DATE` as the two shipped precedents; `_find_install_history_cutover` reading `installs.jsonl`. | yes |
| D-4 | Should the two open questions be reopened or re-answered? | Left exactly as authored, both `Blocking: no`. | Reopening OQ-01: REJECTED, its resolution is correct that the mandatory-marker rule is Order 01's spec approval to make, and it honestly records the consequence if the marker reading was ratified (a working check with a largely inert requirement half, remedied by a follow-up item rather than a silent widening). Reopening OQ-02: REJECTED, its set-level reading is verified correct against `_ORCH_ROW_RE` and is consistent with `SPEC-PLAN-COUNT`'s existing set-level reading. | `ipd_lint._ORCH_ROW_RE`'s literal form; `[Must]` measured in 2 of 12 approved specs; the 2026-09-10 ruling (plan `qhy3i3` OQ-01) that a non-blocking question does not force `no-go`. | yes |
| D-5 | Verdict and readiness, given one HIGH and four lesser findings all now fixed and no blocking open questions. | `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`. | `REJECT - NEEDS REPLAN`: REJECTED, the design is sound, the hinge argument (F-02) holds on measurement, and every finding was repairable by strengthening existing items; nothing about the approach needed rethinking. `REVIEWED - OPEN QUESTIONS`: REJECTED, both OQs are `resolved` and non-blocking. Bare `NO-GO`: REJECTED, the workflow reserves it for genuine not-ready conditions and a reviewed clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`. | Workflow readiness vocabulary; zero findings left OPEN or DEFERRED at or above the default `HIGH` gate threshold, so no escalation to a `Blocking: yes` question is owed; `aw ipd lint` clean at `author` and `review-finalize`. | yes |
