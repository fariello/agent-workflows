# Review findings: plan d1u4sy

- Subject-Id: d1u4sy
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a4808752`. The plan on disk was byte-identical to the sealed lane input
(`source_sha256` `b2f84981a29ac32961b9d7782bb53149320e23f7cc6886c8dba06fa83d2ec0e1`) and
`git status --short` was empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, and `--phase review-finalize`
conforms after the revisions, so nothing found here was structural.

DISCLOSURE: the same agent/model authored this Set, so this is a SELF-REVIEW. Its value therefore rests
on EXECUTING the plan's claims rather than re-reading them, and that is what this round did: every
resolver the Set names was CALLED in-process against this Set's own files, the carrier predicate was
driven with a simulated post-retirement index, and the probe payload was rendered on purpose-built
fixtures. Four of the eight findings below are things the prose asserted and the code contradicted.

THIS SET SHOULD EXIST AND ITS THESIS IS SOUND. The premise was verified rather than accepted:
`runner_shared.evaluate_set_retirement` decides on four facts and never opens the parent's checklist;
`ipd_lifecycle.ROLLUP_OMITTED_GATES` names `pre-transition-ev-checkpoint` as "THE ONE DELIBERATE
DIFFERENCE"; and commit `8b4e1570`'s message says verbatim "Its own `E-*`/`V-*` items were NOT
performed". So parent-carried work genuinely cannot be performed, and a typed row genuinely removes the
place to park it. The parent being authored IN its own grammar is the right call and gave this review a
live fixture to measure against. R1b's delegation of whole-Set verification to child 05 matches the
`svacmz` precedent, which I confirmed carries `- Item-Dependencies: executed:skn8uk, executed:ty7w6o,
executed:dy9ymn`.

WHERE THIS REVIEW SPENT ITS EFFORT: one BLOCKER that the Set inflicts on itself through its own
mechanism, one HIGH that would have dead-ended the first child's executor, and one HIGH that would have
produced a green test proving nothing.

**1. The Set's own thesis, applied to its own front matter, was violated (PR-001, BLOCKER).** Seven
deferred rows across the Set carried `- Carrier: d1u4sy`, naming the orchestrator. That is legitimate on
the day it is written and becomes a DEAD CARRIER at the instant the runner retires the parent, because
`check_engine._CARRIER_TERMINAL_STATUSES` contains `executed` and `_resolve_carrier` refuses a carrier
whose only resolution is terminal. I did not reason about this; I drove
`evaluate_carrier_obligation` against the real files with `d1u4sy` mapped to `executed`, and both
self-carried rows on the parent flipped `True` -> `False` with "carrier d1u4sy resolves only to a
terminal/hidden artifact (executed); nothing revisits it". The failure mode is exactly the one the Set
exists to prevent: an obligation that vanishes at the moment no agent turn is left to notice. Repointing
at siblings was NOT sufficient and I checked: simulating the WHOLE Set executed left three rows still
dead, because a sibling is terminal too once the Set completes. Fixed by pointing the three
Set-outliving obligations at `- Carrier-Evidence:` on the approved spec (verified resolvable via
`resolve_evidence_artifact`) and the rest at durable backlog items `rmcqw8` / `wtd5m2`. Now 0 failures
both today and under full-Set-executed simulation.

**2. All six plans failed the finalize gate on their own open question (PR-002, BLOCKER).** Measured, not
predicted: `aw ipd lint --phase pre-transition` exits 1 on every plan in the Set reporting
`check.ipd-uncarried-obligation`, because each carries an `OQ-01` with `Status: open` and no carrier
field. The severity is `error`, not the grandfathered `info`, because
`check_engine.CARRIER_CUTOVER_DATE` is `20260919` and these plans are dated 2026-09-19 -- they are the
FIRST plans in the repository on the far side of that cutover. Measured: 6 error-tier plans repo-wide,
and all six were this Set. So the Set as authored could not have finalized any of its children. Fixed
per plan on its merits (four self-closing `Carrier-Declined`, two `Carrier-Evidence` on the spec);
`aw check all` fell 247 -> 241 and the rule now fires on none of the six.

**3. Child 01's named resolver cannot return the value it is told to resolve (PR-003, HIGH).** E-02 said
to resolve `<child-id6>` "using `ipd_set_plan.parse_child_table`". Called on this Set's own parent, that
function returns `rows={'1': (), '2': (), '3': (), '4': (), '5': ()}` and its NamedTuple `_fields` is
exactly `('rows','reason')` -- NO id6 anywhere in the return value. Its `order_to_id` parameter is an
INPUT the caller must already possess; supplying it only changes how the Depends-on cells resolve. An
executor following the instruction literally hits a dead end and is then pushed toward the fresh scan the
same item forbids, i.e. straight into the R3 violation the child exists to prevent. The Id cells live in
`runner_shared.child_table_rows`, which is ALREADY the shared row-walk behind the probe cache and
`parse_declared_child_orders`. Compounding it (F-8): SIX OF TWELVE live orchestrators declare no `Id`
column at all, so a resolver assuming one either crashes or vacuously passes on half the population --
the same hazard `parse_declared_child_orders`' docstring records for `rununify`. E-02 and V-02 now name
the correct composition and require the no-`Id` refusal as a fourth case drawn from a real plan.

**4. Criterion 9's test would have been green while proving nothing (PR-005, HIGH).** Three plans required
proving the probe still blocks on an obligation "in its continuation lines or its `## Completion criteria`
section". Both halves are wrong, measured: `orchestrator_probe_excerpt` on a fixture whose
`## Completion criteria` read "SOMEONE MUST MIGRATE THE DATABASE BEFORE ANY CHILD RUNS" renders an excerpt
NOT CONTAINING that string, because `probe_cache_payload` returns only `e_items` and `child_table_rows`;
and a `- Key: value` continuation line is invisible too, because `e_item_action_blocks` stops at the first
line matching `ipd_lint._SUBFIELD_RE`. Verified both directions on a synthetic fixture: a BARE indented
line IS in the payload, the same words as `- Context:` are NOT. This has a sharp consequence the Set had
not stated: the parent's own conforming rows reduce its probe payload to five bare `CONFIRM ... REACHED
executed` strings, every `- Context:` line gone. So the typed row moves the relocated meaning out of reach
of BOTH controls, and child 04's "relocate into continuation lines" guidance needs a bare-line preference.
All three plans now demand a bare indented line and forbid the prose-section fixture.

**5. Child 02 was aimed at a step index no reviewer reads (PR-007, HIGH).** It declared
`.aw/system/workflows/plan-review-long/plan-review-long.md`. That file exists but is a step INDEX; the
reviewer-facing files are `01`/`02`/`03`. `tests/test_plan_review_parity.py::OrchestratorIsNotAStepFileTests`
exists precisely to catch this and its docstring records that the mistake "has been made twice", with the
consequence that "a directory-level parity check looks green" while long-form reviewers get nothing. Also
(F-7): a parity test ALREADY EXISTS and its docstring defines what may be pinned (load-bearing tokens
only, never descriptive wording), so the correct change is one token in an existing list, not a new parity
file. Scope-Paths now names `02-review-and-revise.md`, `03-resolve-and-finalize.md` and
`tests/test_plan_review_parity.py`, and the validation requires RUNNING that test rather than eyeballing a
diff.

**6. Two measurements were stated more confidently than they hold (PR-004, PR-008).** "476 lines" across
the seven probe functions is an AST SPAN; non-blank is 442 and non-blank-non-docstring is 315, so the
figure is right but the unit was unstated in three plans. And "32 rows" is the spec's DATED snapshot: the
corpus is 38 rows across 12 orchestrators today, which sibling `68uhp0` already records, so two plans were
quoting a stale denominator while a third had the current one. The NUMERATOR (zero conforming) is the
load-bearing half and is unaffected.

**7. One real hazard the migration child had not seen (PR-006, MEDIUM).** Rewriting a row changes an
E-item's ACTION TEXT, which `ipd_lifecycle.frozen_region_digest` covers, so it STALES any live begin
receipt. Verified: swapping a child id6 in one row CHANGES the digest while adding a bare continuation
line does NOT. That is the actual mechanism behind child 04's OQ-01 mid-flight question, which had treated
the case as "purely a checklist edit". Eleven of twelve orchestrators are `approved`/`reviewed` rather
than mid-execution, so this is rare rather than impossible; E-02 and V-02 now require a per-plan
live-receipt check.

WHAT I DELIBERATELY DID NOT CHANGE. The Set's shape (one rule, two consumers, migration, cross-Set proof)
is correct and I found no reason to re-cut it. The parent carries no work of its own, which is right. I did
not touch the semantic probe or its tests, and I did not relax any criterion: every finding was fixed by
making a demand MORE specific, never by lowering one. Criterion 9 in particular is now harder to satisfy
than as authored, which is the point.

VALIDATION RUN AT REVIEW. `python3 -m pytest` BARE: `7306 passed, 3 skipped, 2 xfailed in 107.08s`, fully
green, no pre-existing failures to discount. `aw check all --agent`: 247 findings before, 241 after, with
the six `check.ipd-uncarried-obligation` errors on this Set eliminated and no new rule introduced.
`aw ipd lint --phase author` and `--phase review-finalize` conform on all six plans.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness); project carrier contract | `check_engine._CARRIER_TERMINAL_STATUSES`; `_resolve_carrier`; `d1u4sy` Deferred rows 2 and 4 | Seven deferred rows across the Set named `- Carrier: d1u4sy`, the orchestrator the runner RETIRES programmatically. A carrier resolving only to a terminal artifact is refused, so each obligation dies at the exact moment no agent turn remains to notice -- the Set's own failure mode inflicted on its own front matter. Repointing at siblings is insufficient: simulating the whole Set executed left three rows still dead. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Three Set-outliving obligations repointed to `- Carrier-Evidence:` on approved spec `r07vma` (verified resolvable); the rest to durable backlog `rmcqw8`/`wtd5m2`. A prohibition on self-carriers, with the measurement, added to the parent's Deferred preamble. 0 failures today AND under full-Set-executed simulation. |
| PR-002 | BLOCKER | UNDER-SCOPE | G (executability); `check.ipd-uncarried-obligation` | `aw ipd lint --phase pre-transition` exit 1 on all six plans; `CARRIER_CUTOVER_DATE = "20260919"` | Every plan in the Set carried an `OQ-01` with `Status: open` and no carrier field, so all six FAILED the pre-transition finalize gate at `error` severity. These are the first plans in the repo past the carrier cutover, so none of the grandfathering applies. As authored the Set could not have finalized any child. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | A carrier added per plan on its merits: four self-closing `Carrier-Declined` (the decision is made and recorded during that plan's own execution), two `Carrier-Evidence` on the spec for obligations that outlive the Set. Rule now fires on none of the six; `aw check all` 247 -> 241. |
| PR-003 | HIGH | IN-SCOPE | C (architecture); R3 | `ipd_set_plan.ChildTableResult._fields == ('rows','reason')`; `parse_child_table(d1u4sy)` -> `rows={'1': (), ...}`; `runner_shared.child_table_rows` | Child 01 E-02 instructed the executor to resolve `<child-id6>` via `parse_child_table`, which returns NO id6 in any form; `order_to_id` is an input, not an output. The executor dead-ends and is then pushed toward the fresh scan the same item forbids, i.e. into the R3 drift the child exists to prevent. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 rewritten to name the correct composition (`child_table_rows` for Id cells, `parse_child_table` for the order graph and refusal reason), with the in-process measurement pasted. V-02 now FAILS a validation that cites `parse_child_table` as the id6 source. New findings F-7/F-8 recorded in the child. |
| PR-004 | MEDIUM | IN-SCOPE | E (verification); measurement honesty | AST span 476 vs 442 non-blank vs 315 non-docstring; 38 rows / 12 orchestrators vs the spec's 32 | Two figures were stated without their unit or their date. "476 lines" is an AST span, not code lines. "32 rows" is the spec's dated snapshot; the corpus is 38 across 12, which a sibling already records, so two plans quoted a stale denominator. The zero-conforming numerator is unaffected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The span figure qualified in all three plans with all three counts stated; the 32 denominator replaced by the re-measured 38/12 with an instruction to re-derive rather than quote either. |
| PR-005 | HIGH | IN-SCOPE | E (verification); criterion 9 | `orchestrator_probe_excerpt` on a `## Completion criteria` fixture omits the obligation; `e_item_action_blocks` stops at `ipd_lint._SUBFIELD_RE`; `probe_cache_payload(d1u4sy)` yields five bare strings | Three plans required proving the probe blocks on an obligation in a continuation line OR `## Completion criteria`. The section is not in the payload at all, and a `- Key: value` continuation line is invisible too. Only a BARE indented line works, so the test as specified would have passed while demonstrating nothing. The interaction also means a conforming typed row shrinks the parent's payload to almost nothing, moving relocated meaning out of reach of both controls. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Criterion 9 and the E/V items in children 03 and 05 now REQUIRE a bare indented line, forbid the prose-section fixture, and require the limit be reported. Child 04's relocation guidance now prefers a bare line over `- Context:` for obligation-bearing text. The measurement is recorded in the parent's Cross-IPD validation. The probe payload was NOT widened (pre-existing limit `rmcqw8`; widening it one-sidedly is pinned against). |
| PR-006 | MEDIUM | UNDER-SCOPE | A (correctness); lifecycle | `ipd_lifecycle.frozen_region_digest` covers E-item action text; measured digest change on an id6 swap, no change on a bare line | Rewriting a row STALES any live begin receipt, which is the real mechanism behind child 04's mid-flight OQ-01. That plan treated the case as "purely a checklist edit", which is true of the file and false of the receipt. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The measurement and the safe ordering added to child 04's conventions; OQ-01's rationale sharpened to a per-plan mechanical question; V-02 now requires a per-orchestrator live-receipt statement. |
| PR-007 | HIGH | IN-SCOPE | G (executability); parity | `tests/test_plan_review_parity.py::OrchestratorIsNotAStepFileTests` and its docstring; the `plan-review-long/` listing | Child 02 declared `plan-review-long.md`, a step INDEX no reviewer acts on. An existing test exists solely to catch this and records that the mistake "has been made twice", the consequence being a green parity check while long-form reviewers receive no instruction. The plan also proposed a new parity test where one already exists with a documented rule about what may be pinned. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Scope-Paths repointed to `02-review-and-revise.md`, `03-resolve-and-finalize.md` and the existing `tests/test_plan_review_parity.py`. E-01 now says where each half goes. Validation requires RUNNING the parity test and explicitly FAILS a `plan-review.md` vs `plan-review-long.md` comparison. F-7 records the token-list rule. |
| PR-008 | LOW | IN-SCOPE | F (honesty about assurance) | grep for a workflow-body executor in `agent_workflows/` returns only docstrings and CLI help | Child 02's deliverable is PROSE an agent follows, so its assurance ceiling is lower than its siblings' and the run-side gate in child 03 is what actually enforces the invariant. The Set read the two as equally load-bearing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-8 in child 02 so the Set's own assurance story is honest. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What durable carrier should hold the three obligations that outlive the whole Set, given every plan in it becomes terminal? | `- Carrier-Evidence:` naming approved spec `r07vma`, whose own OQ-01 and Section 3a limit 2 ARE those obligations and which no plan in this Set transitions. | A sibling plan (rejected: measured dead once the Set completes). Filing three new backlog items (rejected: the spec already records each question, so a new item would duplicate an existing record and need its own dangling check). `Carrier-Declined` (rejected: these genuinely outlive the Set, so declining would be false). | `check_engine.resolve_evidence_artifact` returns True for the spec path; `_CARRIER_TERMINAL_STATUSES`; simulation of the full Set executed leaves 0 failures | yes |
| D-2 | Should child 02 declare `plan-review-long.md` or the long variant's step files? | The step files `02-review-and-revise.md` and `03-resolve-and-finalize.md`. | Keeping the index path (rejected: an in-tree test exists solely to refuse instructions placed there). Declaring all four step files (rejected: `01-discover-and-snapshot.md` is snapshot/scope work this change does not touch, so declaring it would force a `--scope-ack` for nothing). | `tests/test_plan_review_parity.py::OrchestratorIsNotAStepFileTests` docstring: "a naive parity check passes ... while long-form reviewers receive no instruction" | yes |
| D-3 | Criterion 9 says the probe must still block on an obligation in a continuation line. Which continuation-line shape counts? | A BARE indented line only; `- Key: value` and prose sections are excluded and the plans now say so. | Accepting any continuation line (rejected: measured invisible to the payload, so the test would be a false green). Widening `probe_cache_payload` to cover prose (rejected: payload and cache key must move together, and a one-sided widening is pinned against by `TheExcerptHasAKnownLIMIT`; tracked as `rmcqw8`). | `orchestrator_probe_excerpt` rendered on two purpose-built fixtures; `e_item_action_blocks` stops at `ipd_lint._SUBFIELD_RE`; `probe_cache_payload(d1u4sy)` returns five bare strings | yes |
| D-4 | Should the "476 lines" probe figure be corrected or qualified? | Qualified, keeping 476 as the AST span and stating the 442 and 315 alternatives, rather than replacing it. | Replacing it with 442 (rejected: 476 is correct for the span it measures, and the spec and three plans already cite it, so a swap would create a new inconsistency rather than remove one). | AST measurement of all seven functions at HEAD and at `21eff5d8`, identical | yes |
| D-5 | Child 01's OQ-01 asks where the shared function should live. Should the review decide it? | No. Left to the executor as the plan intended, and given a self-closing `Carrier-Declined` instead of a carrier. | Deciding the siting here (rejected: R3 is satisfied either way, so this is an implementation choice, and the plan's V-04 already records where it went). | spec `r07vma` R3; the plan's own V-04 evidence requirement | yes |
