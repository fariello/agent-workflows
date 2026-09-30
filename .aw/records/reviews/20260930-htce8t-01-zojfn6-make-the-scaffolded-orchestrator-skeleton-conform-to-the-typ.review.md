# Review findings: plan zojfn6

- Subject-Id: zojfn6
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-911 (MEDIUM, fixed), PR-912 (MEDIUM, fixed), PR-913 (MEDIUM, fixed), PR-914 (LOW, fixed), PR-915 (LOW, fixed)

## Round 1

Reviewed at HEAD `03e53ab7` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `clean` after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator row check does not apply to it (verified directly, and recorded in the plan because this is
the plan that CHANGES that gate).

THIS IS AN UNUSUALLY WELL-EVIDENCED PLAN AND ALL EIGHT FINDINGS REPRODUCE. I re-drove every one rather
than reading it. F-1: `orchestrator_row_conformance(build_skeleton(kind="orchestrator", ...))` returns
`conforming=False` with row `E-01` refused `not-a-typed-child-tracking-row` AND the empty-table
`table_reason`, exactly the two independent counts the plan claims. F-2: the per-checkpoint `IPD-S407`
counts are `author` 0, `review-finalize` 1, `pre-execution` 0, `pre-transition` 1, `post-transition` 0,
and `_ORCH_ROW_BLOCKING_CHECKPOINTS` is `frozenset(("review-finalize","pre-transition"))`, so the gate
really is open at `begin`. F-3: `tests/test_orchestrator_row_grammar.py` does not exist and
`grep -rn "SHIPPED_SCAFFOLD" tests/` returns nothing, so the backlog item's promised safety net is
absent as the plan says. F-4: the named test is indeed now
`test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence`, and with
`pre-execution` monkeypatched in it PASSES (`1 passed in 0.24s`). F-7: deleting the exec leaf yields
`IPD-I303`. F-8: a scaffolded plan with a placeholder child id6 raises no new `aw check plans` finding.

F-5 IS THE CLAIM MOST WORTH RE-DRIVING AND IT IS EXACT. Under a prototype patching `build_skeleton` to
emit the conforming shape plus adding `pre-execution` to the constant, the bare suite reported
`6 failed, 3381 passed`, and the six failures are the SAME six test identities the plan names. I then
carried the prototype further than the plan's author did, repairing the anchors as E-05 prescribes:
moving the two prose anchors drops it to `2 failed`, and adding the untyped-row injection reaches 0 for
`test_orchestrator_retirement.py`, leaving exactly `test_orchestrator_template_matches_generator` as the
single residue that E-04's regeneration closes. So the plan's "1 failed, then regenerate" path is
verified end to end, not merely asserted. The untyped-row refusal test still PASSES on a genuinely
untyped fixture after the injection, which is the vacuous-pass hazard V-05 exists to catch.

E-02's PRESCRIBED FIX WORKS AS WRITTEN. I built it: replacing the row with
`- [ ] E-01 CONFIRM c0ch01 REACHED executed` and the prose placeholder with a five-column table carrying
an `Id` cell naming the same token yields `conforming=True`, empty `table_reason`, and a row whose
`(child_id6, status, depends_on)` resolve to `('c0ch01','executed','none')`. `kind="child"` still returns
`applies=False`. E-03's expectation also holds: `authoring_placeholders_resolved` returns False for both
kinds after the change, so that item genuinely is a CONFIRM rather than an edit. E-02's "orchestrator
ONLY" instruction is achievable because `kind` is in scope at the `_exec_placeholder_leaf()` call site in
`build_skeleton`, which I checked rather than assumed since that helper takes no arguments today.
OQ-01 verifies: `c0ch01` collides with no tracked `- Id:` value and `is_valid_id6` accepts it.

THEN I AUDITED WHAT THE PLAN DID NOT PRESENT, which produced the three MEDIUM findings.

FIRST, THE BLAST RADIUS IS WIDER THAN `aw ipd begin`. The plan frames E-06 entirely around that one
command, and `runner_shared`'s pre-queue pre-flight also lints at `pre-execution`, specifically
`checkpoint = "pre-execution" if status in ("approved","auto-approved") else "author"`, reporting
`[RUN-STRUCTURE-PREFLIGHT] ipd <id6> ... violates <code>`. So after E-06 an APPROVED non-conforming
orchestrator is refused at QUEUE BUILD, before any agent turn is spent. That is desirable behavior and it
is a bigger change than the plan describes, and it makes E-01's census incomplete: conformance alone does
not tell you whether the gate would refuse anything, because the gate keys on STATUS too. Measured safe
today (7 live pending orchestrators, statuses `reviewed` 2 and `to-review` 5, `approved` 0, all
conforming), so nothing existing is refused; but E-01 now censuses status as well, and an `approved`
non-conforming orchestrator is named as a STOP condition rather than a note.

SECOND, THE `author` PARAGRAPH IS AS STALE AS THE ONE E-06 EXISTS TO FIX, and E-06 explicitly said to
leave it alone. That comment justifies its exclusion with "11 of the 12 live pending orchestrators do not
conform ... and 6 of the 12 additionally declare no `Id` column at all" and warns of turning `aw check`
red "on eleven other agents' APPROVED plans before the migration that fixes them (child `68uhp0`) has
run". Measured: 7 live pending orchestrators, 0 non-conforming, 0 without a parseable `Id` table, and
`68uhp0` is `executed`. I also checked the structural half, because it decides whether the exclusion is
still right for a DIFFERENT reason: `check_engine.check_ipd_lint_reach` is PENDING-LANE ONLY
(`"pending" not in p.parts: continue`), so the 52 non-conforming `executed` plans are outside the sweep
by construction and cannot go red regardless. The conclusion is deliberately narrow: this does NOT argue
for gating `author` (that needs its own blast-radius measurement and the plan correctly fences it out),
but leaving the spent numbers in place would have this plan land a fix for exactly one stale comment
while leaving its neighbour asserting a dead corpus fact. E-06 now refreshes the figures and explicitly
does not touch the exclusion.

THIRD, THE FIXTURE THE SCOPE CHECK CLEARS IS CLEARED FOR THE WRONG REASON. The plan says
`tests/fixtures/conforming-orchestrator.md` is safe because "the suite passed with it untouched under the
prototype". True, but the reason matters: that fixture is itself NOT row-conforming
(`conforming=False`, row `E-01` `not-a-typed-child-tracking-row`, same empty-table `table_reason` as the
scaffold), and it survives only because `lint_file(..., checkpoint="author")` returns `conforming` and
`author` is the ONLY checkpoint its three consumers use. So its NAME asserts a property it does not have,
and the first plan to add `author` breaks all three at once, including the `EXITS` table's positive row
whose own comment reads "Every nonzero row is vacuous while this is broken". The plan should record that
consequence rather than the reassurance, and should still leave the fixture alone, which is what it now
does.

FOUR FIGURES HAVE DRIFTED, which is the repository's re-derivation convention rather than an authoring
error, and they matter here because two were written as ACCEPTANCE BARS. The pending census moved 3/3 to
7/7 (still all-conforming, so the property held while the count did not); the suite baseline moved
`3246 passed` to `3387 passed`; `aw check all` moved 33 findings to 61 (top rules
`check.plan-spec-link-missing` 35, `check.ipd-uncarried-obligation` 10,
`check.lifecycle-transition-invalid` 5, `check.ipd-lint-diagnostic` 5), with zero `IPD-S407` in both
measurements; and tracked `- Id:` values moved 1801 to 1885. An executor comparing against the authored
numbers would have read every one of those as a regression they caused.

WHAT I CHECKED AND LEFT ALONE. The three `Carrier-Declined` rows all argue their case properly, and the
terminal-bucket one is right on the mechanism I verified (a terminal plan is never begun, so
`pre-execution` cannot gate it). The `u8dl3q` carrier for OQ-01-in-full resolves. The conventions section
is accurate, including that a deleted checklist is refused by `IPD-I303` at `author`, that
`ORCH_ROW_CANONICAL` exists as the natural seam for the render-from-one-source refactor, and that the
templates are generated rather than hand-maintained. The spec-sync section's claim that `ipd-spec` carries
no prose copy of the row grammar is correct. E-05's "three anchors" is a correct count of BROKEN anchors:
there is a fourth substitution (`- Highest E allocated: 01`) which E-02 does not disturb because it is
metadata, and I recorded that so an executor does not hunt for a fourth repair. I also found a second
consumer inside the untyped test (an `assertIn` on the literal untyped row) that E-05 did not name and
that my own prototype tripped over, and recorded it.

Nothing in `agent_workflows/` or `tests/` was modified. All prototype work lived in a throwaway pytest
plugin outside the repository; `git diff --stat agent_workflows/ tests/` is empty.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-911 | MEDIUM | UNDER-SCOPE | C. Architecture / G. Executability (an undeclared consumer of the gate being changed) | `runner_shared` pre-flight: `checkpoint = "pre-execution" if status in ("approved","auto-approved") else "author"`, reporting `[RUN-STRUCTURE-PREFLIGHT] ipd <id6> ({rel_path}) in status {status} violates {d.code}`. Censused pending orchestrators: 7 live, statuses `reviewed` 2 / `to-review` 5 / `approved` 0, all conforming | **E-06 is framed entirely around `aw ipd begin`, but adding `pre-execution` also arms the runners' pre-queue pre-flight for every `approved`/`auto-approved` plan.** That is a refusal at QUEUE BUILD, before any agent turn, and it means E-01's conformance-only census is insufficient to establish safety: the gate keys on STATUS as well, so "all pending conform" and "no approved plan is refused" are different claims. Nothing is refused today, but the plan cannot show that because it never measured status | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-9 records the mechanism and the measured status distribution. E-01 now censuses status beside conformance and names an `approved` non-conforming orchestrator as a STOP condition. V-01 requires the status distribution pasted. V-06 gains a fourth artifact requiring `lint_file(..., checkpoint="pre-execution")` on an untyped orchestrator, so the runner path is exercised rather than inferred from the `begin` case |
| PR-912 | MEDIUM | UNDER-SCOPE | D. Anti-regression / honest documentation | The `author` paragraph claims "11 of the 12 live pending orchestrators do not conform ... 6 of the 12 additionally declare no `Id` column" and warns of going red "on eleven other agents' APPROVED plans before the migration that fixes them (child `68uhp0`) has run". Measured: 7 live pending orchestrators, 0 non-conforming, 0 with an unparseable `Id` table; `68uhp0` is in `executed/`. `check_engine.check_ipd_lint_reach` is pending-lane only (`"pending" not in p.parts: continue`), so the 52 non-conforming `executed` plans are outside the sweep | **The `author` exclusion's recorded justification is now as stale as the `pre-execution` one E-06 exists to fix, and E-06 instructed leaving it untouched.** The plan would therefore land a fix for one spent comment while leaving its immediate neighbour asserting a dead corpus fact, which is the same "codebase asserting a state that no longer holds" defect its own spec-sync section names as the reason E-06 is necessary | C:Low; U:Low; S:Low; F:Low; Overall:Low-Medium | FIXED | F-10 records the measurement and the pending-lane scope. E-06 narrowed: refresh the `author` paragraph's FIGURES, replacing them with the property and the structural sweep-scope reason, while explicitly NOT changing the exclusion, not adding `author` to the constant, and not asserting it should be added. Its Expected outcome now requires no stale count in EITHER paragraph. The Deferred row is reconciled so it does not read as contradicting E-06, and states honestly that the exclusion now rests on sweep scope rather than on a live false-positive count |
| PR-913 | MEDIUM | IN-SCOPE | E. Testing (a safety clearance whose stated reason does not establish safety) | `orchestrator_row_conformance` on `tests/fixtures/conforming-orchestrator.md`: `conforming=False`, row `E-01` `not-a-typed-child-tracking-row`, `table_reason` "section present but contains no parseable table row". `lint_file(..., checkpoint="author")` returns `conforming`. Consumers: `test_ipd_lint.py` twice at the `author` phase plus the `EXITS` positive row, and `test_ipd_schema.py`, all via `tests.support.CONFORMING_ORCHESTRATOR` | **The Scope check clears this fixture because "the suite passed", which is true but is not the reason it is safe.** It is safe only because `author` stays excluded and that is the only checkpoint its consumers use. The fixture's NAME asserts a row conformance it does not have, so the next plan that adds `author` breaks three consumers at once, including a positive exit-code row whose own comment says every nonzero row is vacuous while it is broken. A reader of this plan would conclude the fixture is conforming | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The Scope check now enumerates the COMPLETE consumer set from a repository-wide grep rather than naming two examples, and replaces the reassurance with the measurement: the fixture is not row-conforming, it survives only because `author` is excluded, and the consequence for a future `author`-widening plan is stated. It is still deliberately left alone, with the reason (renaming or retyping it is the `author` decision this plan fences out) |
| PR-914 | LOW | IN-SCOPE | E. Testing / live-artifact criteria (four drifted counts, two used as bars) | Re-derived at review: pending census 3/3 to **7/7**; bare suite `3246 passed, 2 skipped` to **3387 passed, 2 skipped**; `aw check all --agent` 33 to **61** findings (zero `IPD-S407` in both); tracked `- Id:` values 1801 to **1885** | **Two live-artifact counts are written as acceptance bars ("must be no worse than its 33-finding baseline", "Baseline ... 3246 passed") and all four have drifted.** An executor comparing against them would read ordinary repository growth as a regression their change caused, and the `aw check all` case is the worst: 61 against a stated 33 looks like 28 new findings | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four restated as properties with both dated measurements and an explicit instruction that drift is expected: F-6 names "every LIVE pending orchestrator conforms" as the durable claim; the suite bar becomes zero failures rather than a count; the `aw check all` bar becomes a RULE-ID SET comparison with no `IPD-S407` and no new rule id; OQ-01's bar becomes the no-collision property. E-01, V-01 and V-06 updated to match |
| PR-915 | LOW | IN-SCOPE | G. Plan executability (a gate missing four required elements, plus two executor traps) | The gate had no honesty MUST, no scope fence, no open-questions statement, and its transition read "moves this plan to `.aw/records/plans/executed/` only after ..." with no conditional runner/executor ownership and no never-hand-roll prohibition. Measured: a raw scaffold at `pre-execution` yields `IPD-S404`, `IPD-M106`, `IPD-M110`, `IPD-M111` and `check.ipd-dependency-unresolved`. `_structurally_conforming_plan` has a fourth substitution (`- Highest E allocated: 01`) E-05 does not mention, and the untyped test carries an `assertIn` on the literal untyped row that E-05 also does not mention | **Four missing execution-contract elements and two traps an executor walks into.** V-06 asks for a scaffolded orchestrator "NOT refused", but a raw scaffold IS refused at `pre-execution` for five unrelated reasons, so the assertion had to be narrowed to the absence of `IPD-S407`. E-05's anchor list omits an `assertIn` that my own prototype tripped over, leaving exactly that one test red after the other five were green | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the paste-the-actual-output honesty MUST (naming V-05's vacuous-pass hazard), the explicit `aw commit zojfn6 -- <five paths>` line, a declaration-style scope fence naming the TWO genuinely-unsafe stop conditions, the open-questions statement, and the unconditional-finalize/conditional-owner paragraph with the never-hand-roll prohibition; plus a note that this plan is `- Kind: child` so the gate it creates cannot refuse its own `begin` (verified). V-06 case (2) narrowed to the absence of `IPD-S407` with the five expected codes named. E-05 records the non-broken fourth substitution and the `assertIn` consumer, with the measured 6-to-2-to-0 failure path |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-912: the `author` paragraph's corpus justification is spent. Leave it as E-06 instructed, refresh only the figures, or widen `author` too? | REFRESH THE FIGURES ONLY, leaving the exclusion and its structural reasoning untouched | (a) leave the whole paragraph alone as authored; (b) also add `author` to the constant, since 0 of 7 pending orchestrators would go red | Option (a) has this plan fix one stale comment and leave the adjacent one asserting a dead fact, which the plan's own spec-sync section names as the reason E-06 exists ("leaving the comment would leave the codebase asserting a state that no longer holds"). Option (b) is a real possibility now that the false-positive count is zero, and it is refused here because the exclusion's live reason is the sweep's PENDING-LANE scope, which I verified and which this plan has taken no measurement of the blast radius for; the plan's Deferred row fences that decision out and `25kzda` 2.5b records where mass false-refusal leads. Refreshing a spent number is not widening a gate | yes |
| D-2 | PR-913: the fixture named `conforming-orchestrator.md` is not row-conforming. Rename or retype it here? | NO; record the measurement and the future consequence, leave the file alone | (a) rename it to `nonconforming-rows-orchestrator.md`; (b) give it typed rows so the name becomes true; (c) leave the authored "the suite passed" reassurance as-is | Options (a) and (b) both reach outside this plan's declared `- Scope-Paths:` into a fixture with four consumers across two test modules, and (b) in particular would be doing the `author`-widening preparation that the Deferred row fences out, on a corpus measurement this plan has not taken. Option (c) leaves a reader believing the fixture is conforming, which it measurably is not, and leaves the next `author` plan to discover three simultaneous failures including a positive exit-code row. Recording the measurement costs nothing and is what makes the clearance checkable | yes |
| D-3 | PR-911: should E-01's census be widened to status, or is conformance enough to establish E-06 is safe? | WIDEN IT to status, and name an `approved` non-conforming orchestrator as a STOP condition | (a) conformance only, as authored, since all pending plans conform anyway; (b) add a separate E-item for the runner path | Option (a) is safe TODAY by accident rather than by measurement: the runner pre-flight gates at `pre-execution` only for `approved`/`auto-approved`, so the safety claim depends on a field E-01 never read, and a future executor running E-01 on a different tree would get a green census while an approved non-conforming orchestrator sat in the queue. Option (b) would split a two-line addition to an existing census into its own item, against the plan's right-sizing rule, for a measurement that belongs in the census it extends | yes |
| D-4 | Should the review implement E-02 through E-06, having prototyped the whole change end to end? | NO; the prototype stays a throwaway pytest plugin outside the repository | (a) implement it, since the fix is fully measured and reaches a green suite; (b) paste the prototype's source into the plan as the implementation | The workflow edits planning documents only. The prototype also cuts corners the deliverable must not: it monkeypatches `build_skeleton` rather than editing it, re-implements `_structurally_conforming_plan` wholesale instead of moving three anchors surgically, and authors none of the `tests/test_ipd_authoring.py` coverage proposed change 5 requires. What it legitimately contributes is verification that E-02's prescribed shape works, that E-05's repair reaches zero failures in its module, that the residue is exactly the template parity test, and the two anchor traps recorded in E-05 | yes |
