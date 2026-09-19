# Review findings: plan 68uhp0

- Subject-Id: 68uhp0
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c3c337d7`. The plan on disk was byte-identical to the sealed lane input (`diff`
reported no difference) and `git status --short` was empty before any edit, so no pre-review snapshot was
needed. Structural preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0,
both before and after the revisions; the watermark is unchanged at 05, because every finding was fixed by
making an existing instruction more specific rather than by adding an E-item.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on
EXECUTING claims rather than re-reading them. This round parsed every pending `Kind: orchestrator` plan
in-process through `runner_shared.child_table_rows`, counted children against rows, read every child
table header, listed the begin-receipt directory, and REPRODUCED each lint refusal by making the edit the
plan's instruction would produce and linting the result. Six findings are cases where the plan as written
either omitted work the migration cannot succeed without, or instructed an edit that breaks the plans it
touches.

WHAT SURVIVED. The five-item measure-decide-migrate-audit-reconcile shape is right, and its central
judgements are accurate and load-bearing: the population is genuinely unstable and E-01 is right to
re-derive it (re-measured here at 12 orchestrators, 38 `E-*` rows, matching the plan's own authoring
figure exactly); relocation rather than deletion is the correct requirement and the `- Context:` versus
bare-continuation-line distinction the previous round added is real and correctly measured; the three
welded tracking-plus-condition rows named in F-4 are the right examples; and `d1u4sy` is a genuine
control (its five rows are 36 characters each and are the only conforming rows in the corpus).

WHERE THIS REVIEW SPENT ITS EFFORT: four HIGH findings, three of which are work the migration structurally
cannot complete without and which the plan never named, and one of which is an instruction that would
break every plan an executor followed it on.

**1. Six of twelve child tables cannot resolve an id6 at all (PR-401, HIGH).** Child 01's E-02 REFUSES an
orchestrator whose child table has no `Id` column, naming the missing column as the cause. Measured by
calling `child_table_rows` on every pending orchestrator: `5e4sb6`, `ao1rb7`, `a5wdne`, `tb63qv`,
`2xz59a` and `s0gnha` use `| Order | File | What it does | Depends on |` or `| Order | What it does |
Depends on |` and contain no id6 in any cell. So on HALF the corpus no row can be made to conform until
the TABLE is edited, and the plan as authored never mentioned touching a child table. Two further cases
resolve only partially and are worse than a missing column because they look resolvable: `wfjsp4`'s `Id`
cells read `` `y4bdoz` ``, `UNAUTHORED, must be written before this Set runs`, and `` `1bdxcp` (currently
authored as Order 02) ``; and `5e4sb6`'s Order cells include the non-numeric `03+` and `last`, a shape
`tests/test_orchestrator_retirement.py` pins deliberately as "the real `5e4sb6` shape". Adding an `Id`
column is now explicitly in scope; inventing an id6 for an unauthored child is explicitly out, and is an
E-04 escalation.

**2. The migration ADDS rows, and the plan sized itself on rewriting them (PR-402, HIGH).** R1a is one row
per tracked child, so the target row count is the CHILD count. Measured: 38 rows against 49 children,
disagreeing on nine of the twelve plans, with `5e4sb6` at 3 rows for 11 children and `yeh7gc` at 1 for 3.
Two schema consequences follow that the plan never named, and I reproduced both by adding one row to
`d1u4sy`: `IPD-I304 Highest E allocated must be >= the largest present E-* suffix` (six of the twelve
have a watermark below their child count), and `IPD-I303 E-06 has no validation item`. An executor who
rewrote rows one-for-one would leave nine plans tracking fewer children than they have, and one who added
rows without the watermark and V-item work would leave them non-conforming in a new way.

**3. The Scope instructs an edit that breaks every plan it is applied to (PR-405, HIGH).** The Scope line
said to rewrite "each orchestrator's `E-*`/`V-*` rows into the R1a form". Spec R1a specifies the shape for
the `E-*` row only. I made exactly that edit to `d1u4sy` and linted it: writing `- [ ] V-01 CONFIRM
dpdyed REACHED executed` yields `IPD-I302 validation-section leaf must be a valid V-* item` plus
`IPD-I303 E-01 has no validation item`, because `check_ids_and_bijection` requires a validation leaf to
match `V_ID_STRICT` and carry a `validates E-NN` target. So an executor following Scope literally
converts twelve conforming plans into twelve non-conforming ones while believing it satisfied the
grammar. The Scope, E-03 and V-03 now state the boundary explicitly.

**4. The cutover route's cited precedent does not support it (PR-403, HIGH).** E-02 offered a date cutover
"following `check_engine.CARRIER_CUTOVER_DATE`'s pattern". That pattern is a SEVERITY TIER on an `aw
check` finding: `carrier_severity_for_plan` returns `error` post-cutover and `info` before it, and `info`
is the only severity `artifact_core.drift_exit_code` exempts, so a pre-cutover artifact still REPORTS and
merely does not fail CI. Child 03's control has no severity dimension: it is a pre-queue run refusal that
raises before the run directory exists. Child 01's rule is a `C_*` diagnostic in `lint_text`, whose
disposition is `conforming` iff `diags` is empty. There is no `info` tier to demote into, so "a cutover
following that pattern" necessarily becomes a date-conditioned SKIP of the check, which leaves a
pre-cutover orchestrator permanently unchecked rather than temporarily un-failing. That is a materially
weaker mechanism than the precedent, and citing the precedent for it would misrepresent what was built.
E-02 must now say which of the two it means, and V-02 FAILS a route that cites the constant as authority
for a skip.

**5. The disposition record had no named home, and the harmful reading edits twelve other agents' plans
(PR-406, MEDIUM).** E-04 said to record the disposition "in the plan" without saying which. Writing it
into each migrated orchestrator would be an edit well beyond the checklist rewrite this plan is
authorised for, on plans several of which are `approved`. Pinned to this plan's own V-04 evidence block.
One related worry I checked and can rule out: a single `## Workflow history` line on a migrated plan is
SAFE, measured by running `plan_readiness.is_plan_review_approved` against `5e4sb6`, `d1u4sy` and
`s0gnha` with a `- 2026-09-20 migrated (...)` line prepended (all three stayed `True`, and
`check_readiness_attestation` stayed clean). The caveat is worth recording: the leading token must not be
a status word, since that line's shape is what the readiness reader parses.

**6. The begin-receipt hazard is mechanically right and currently empty (PR-407, MEDIUM).** The previous
round added a good finding: rewriting a row moves `frozen_region_digest` and stales a live begin receipt.
I measured its population and it is ZERO, and structurally so rather than by luck:
`ROLLUP_OMITTED_GATES["begin-receipt-requirement"]` records that an orchestrator has no receipt BY
CONSTRUCTION, because nothing calls `aw ipd begin` for a plan no agent executes, and the rollup mints
none. `ipd_lifecycle.receipt_dir` holds 26 receipts and no orchestrator id6 among them. This matters
because the plan's mid-flight framing invited an executor to reason from each plan's Status ("eleven of
twelve are approved or reviewed"), which is the wrong input; the right one is the receipt file. E-02 and
V-02 now demand the receipt directory as the evidence.

**7. Four suite nodes read the live plan tree and the plan named none of them (PR-408, MEDIUM).** This
plan rewrites twelve TRACKED plans, so the tests that can break are the corpus sweeps, and a bare-suite
total hides which. Measured by reading each: `tests/test_ipd_lint.py::test_every_readiness_carrying_plan_in_the_tree_is_attested`
(rglobs `SOURCE_PLANS`), `tests/test_plan_readiness.py::test_no_pending_plan_is_refused_on_a_verdict_today`
and `::test_predicate_over_every_pending_plan_never_raises_and_respects_no_go` (both glob `PENDING_DIR`),
and `tests/test_plan_status.py`'s status drift guard over every plan's `- Status:` (which is the
mechanical reason this plan must not touch a Status). The second is KNOWN FAILING at HEAD on three
`reaskscore` plans another party is editing, proven pre-existing during child 01's review, so E-05 now
requires comparing the NAMED plans rather than the pass/fail bit.

**8. One out-of-scope entry claimed more than it grants, and one deferral was missing (LOW/MEDIUM,
recorded as F-14 and a new deferral row).** The terminal-orchestrator exclusion read as though this plan
were choosing not to migrate history. It is not a choice: `lint_text` short-circuits a terminal-dir file
to `legacy/not evaluated` with zero diagnostics at every phase but `post-transition`, verified by linting
a real executed orchestrator, and child 03's gate reads only the queue. So the 51 terminal orchestrators
carrying 149 `E-*` rows are outside the rule by an EXISTING mechanism. Separately, the plan had no
deferral covering the case where relocation reveals a genuinely uncovered obligation and no sibling can
take it; backlog `wtd5m2` already tracks exactly that for seven of these parents, and a deferral row now
carries it, which closes the gap an executor could otherwise have closed by deleting the text.

WHAT I DELIBERATELY DID NOT CHANGE. The five-item shape and its dependency chain are correct and I did
not split E-03, and the size note now records WHY rather than asserting it: the four obligations review
added to E-03 are constraints on one mechanical pass over one file, all verified by the same `aw ipd
lint` call on that file, whereas splitting by concern would leave every plan in a broken intermediate
state between passes. I did not relax any requirement: every edit made a demand more specific, and V-01
through V-05 are each materially harder to satisfy than as authored. OQ-01 stays `open` and non-blocking,
because the ROUTE is genuinely E-02's to choose and the maintainer may prefer a different disposition,
but I removed the unknown from it by measuring the receipt population.

VALIDATION RUN AT REVIEW. `aw ipd lint --phase author --agent` conforms before and after the revisions
(exit 0, 0 findings, watermark unchanged at 05). Every mechanical claim above was produced by running
code in-process against the real corpus, not by reading it: `child_table_rows` over all twelve
orchestrators for the header and id6 census; row counts against child counts; `ipd_lint.lint_text` on the
three synthetic edits that produce `IPD-I302`, `IPD-I303` and `IPD-I304`; `ipd_lint.lint_file` on a real
executed orchestrator for the `legacy/not evaluated` short-circuit; `ipd_lifecycle.receipt_dir` for the
receipt census; and `plan_readiness.is_plan_review_approved` plus `check_readiness_attestation` on three
real plans for the history-line safety check. No suite run is claimed for this review: the revisions are
plan-text only and touch no code, and the plan's own gate requires the bare suite plus the four named
node ids at EXECUTION, where there is a diff to measure.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | UNDER-SCOPE | A (correctness); G (executability) | `child_table_rows` over all 12 pending orchestrators at review: `5e4sb6`, `ao1rb7`, `a5wdne`, `tb63qv`, `2xz59a`, `s0gnha` have no `Id` column; `wfjsp4` Id cells include `UNAUTHORED, must be written before this Set runs`; `5e4sb6` Order cells include `03+`/`last`; child 01 E-02's refusal text | Half the corpus cannot resolve a child id6 at all, so no row on those six can conform until the child TABLE is edited. The plan never mentioned child-table work, leaving an executor blocked on six of twelve plans with the only unblocking move being one the plan forbids (a fresh scan) or one that forges a reference (inventing an id6). | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now censuses the `Id` column per orchestrator; E-03 requires fixing the table first and states adding a column is IN scope while inventing an id6 is OUT; E-04 records an unauthored-child case as ESCALATED; Scope line updated; recorded as F-8 and a Step-0 convention. |
| PR-402 | HIGH | UNDER-SCOPE | A (correctness); D (invariants) | 38 `E-*` rows against 49 children across the 12, disagreeing on 9; added one row to `d1u4sy` and linted: `IPD-I304` plus `IPD-I303 E-06 has no validation item` | The migration mostly ADDS rows (R1a is one row per child), and adding one requires bumping `- Highest E allocated:` (six of twelve sit below their child count) and adding a matching `V-*`. The plan sized and instructed a one-for-one rewrite, so an executor would leave nine plans under-tracking their children or newly non-conforming. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 censuses child count and watermark; E-03 requires the watermark bump; V-01 requires the row-versus-child delta stated; V-03 requires a sample plan whose row count GREW showing both the added V-items and the bump; recorded as F-9 and two Step-0 conventions. |
| PR-405 | HIGH | IN-SCOPE | A (correctness); G (executability) | `ipd_lint.lint_text` on `d1u4sy` with `V-01` rewritten to `CONFIRM dpdyed REACHED executed`: `IPD-I302 validation-section leaf must be a valid V-* item`, `IPD-I303 E-01 has no validation item`; `check_ids_and_bijection` read | The Scope instructed rewriting "`E-*`/`V-*` rows into the R1a form". R1a governs the `E-*` row only, and an R1a-shaped `V-*` row breaks the schema, so an executor following Scope literally converts twelve conforming plans into twelve non-conforming ones while believing the grammar was satisfied. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Scope line corrected to name the `E-*` rows and to require the `V-*` section stay in the schema's `V-NN validates E-NN` form; E-03 carries the measured refusal codes and the positive instruction (keep the header and subfields, add/remove V-items to preserve the bijection, model on `d1u4sy`); V-03 requires `aw ipd lint` conforming per migrated plan as the catch; recorded as F-10. |
| PR-403 | HIGH | IN-SCOPE | C (architecture); honest documentation | `CARRIER_CUTOVER_DATE`, `carrier_severity_for_plan` (`error` post-cutover, `_CARRIER_LEGACY_SEVERITY` = `info`), `artifact_core.drift_exit_code` exempting only `info`; `lint_text`'s disposition rule; child 03's pre-`run_dir` siting | E-02 offered a cutover "following `CARRIER_CUTOVER_DATE`'s pattern", but that pattern demotes a FINDING'S SEVERITY and neither consumer here has a severity dimension, so copying it necessarily yields a date-conditioned SKIP of the check. That is weaker than the precedent (permanently unchecked rather than temporarily un-failing) and citing the precedent for it misrepresents what was built. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now states the precedent does not transfer, requires saying which of the two mechanisms a chosen cutover is, and records that migrate-all is the route the evidence supports (12 plans, not a 106-plan corpus, and nothing left unchecked); V-02 FAILS a route citing the constant as authority for a skip; F-5 rewritten from "a precedent to weigh" to the corrected reading; Step-0 convention corrected. |
| PR-406 | MEDIUM | IN-SCOPE | B (least privilege); C (architecture) | the plan's own E-04 text ("in the plan"); `is_plan_review_approved` and `check_readiness_attestation` run against `5e4sb6`, `d1u4sy`, `s0gnha` with a `migrated` history line prepended (all safe) | The disposition record's home was unnamed, and the harmful reading (write it into each migrated orchestrator) is an edit far beyond the authorised checklist rewrite on plans that are not this plan's to restructure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 pins the record to this plan's V-04 evidence and forbids writing one into a migrated plan; the measured-safe courtesy history line is permitted with the leading-token caveat; V-04 requires confirming no migrated plan received a disposition record and requires the per-file edit list; recorded as F-11. |
| PR-407 | MEDIUM | IN-SCOPE | A (correctness); evidence quality | `ipd_lifecycle.receipt_dir` listing 26 receipts with no orchestrator id6 among them; `ROLLUP_OMITTED_GATES["begin-receipt-requirement"]`; `evaluate_set_retirement`'s four facts | The previous round's begin-receipt finding is mechanically correct but its population is ZERO and structurally so. The plan invited an executor to reason about mid-flight risk from each plan's STATUS, which is the wrong input; the receipt FILE is the right one, and the real mid-flight exposure is child 03's gate refusing a queued parent, which the rewrite fixes. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 censuses the receipt per plan via `receipt_path_for` (checkout-anchored, not lane-anchored); E-02 requires the per-plan answer from the receipt with the structural reason cited; V-02 requires the receipt DIRECTORY as evidence rather than the Status; OQ-01's rationale carries the measurement; recorded as F-12 and a Step-0 convention. |
| PR-408 | MEDIUM | UNDER-SCOPE | E (testing) | each node's source read: `test_every_readiness_carrying_plan_in_the_tree_is_attested` (rglobs `SOURCE_PLANS`), `test_no_pending_plan_is_refused_on_a_verdict_today` and `test_predicate_over_every_pending_plan_never_raises_and_respects_no_go` (glob `PENDING_DIR`), `tests/test_plan_status.py`'s drift guard | The plan asked only for the bare suite. It rewrites twelve TRACKED plans, and exactly four suite members read the live tree; a whole-suite total cannot attribute a corpus regression to this diff, and one of the four is already failing at HEAD for an unrelated reason that would otherwise be misread as damage. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The four node ids named in the validation section and in E-05, to be run before AND after by id; the known pre-existing failure recorded with the instruction to compare the NAMED plans; V-05 requires both outputs pasted; recorded as F-13 and a Step-0 convention. |
| PR-404 | MEDIUM | UNDER-SCOPE | E (verification) | the plan's V-03 as authored ("one nearly schema-shaped, one with a long prose row, one with a welded row"); the measured hard cases | The V-03 sample spanned PROSE LENGTH, which is not where the difficulty is. Three plans chosen on that axis can all be easy plans, leaving the two structurally hard cases (a table with no `Id` column, a plan whose row count must grow) unevidenced. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | V-03 now requires the three to span the measured hard cases by name, and states plainly that a sample of three easy plans does not evidence the item. |
| PR-409 | LOW | IN-SCOPE | F (honest documentation) | `ipd_lint.lint_file` on a real executed orchestrator: disposition `legacy/not evaluated`, zero diagnostics; 51 terminal orchestrators carrying 149 `E-*` rows counted at review | The terminal-orchestrator out-of-scope entry read as a choice this plan was making, when they are outside the rule by an EXISTING mechanism. Stating it as forbearance would claim an exemption this plan did not grant, which is exactly the kind of unearned claim criterion 12 is written to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The out-of-scope entry now cites the short-circuit and the queue-only gate and states no grandfather clause is needed; recorded as F-14 and a Step-0 convention. |
| PR-410 | MEDIUM | UNDER-SCOPE | D (invariants); R2 | backlog `wtd5m2` (`open`, `Blocks-Release: next`) naming seven of these parents and their uncovered items, with the remedy "AUTHOR A CHILD ... DO NOT delete the parents' checklist items" | The plan forbade deletion repeatedly but had no deferral saying where a genuinely uncovered obligation GOES when relocation reveals one and no sibling can take it. A prohibition with no destination is the exact shape AGENTS.md records as getting complied with by deleting the checklist. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | A deferral row added carrying `wtd5m2`, stating the disposition is ESCALATED and the work belongs to that item, so the executor has a destination rather than only a prohibition. |
| PR-411 | LOW | IN-SCOPE | G (executability); scope fence | `ipd_lifecycle._scope_match`'s last line (a literal entry matches by PREFIX, so a directory entry admits the tree beneath it); ~100 non-orchestrator plans in `pending/` | The `Scope-Paths` directory entry puts EVERY pending plan in scope, so the finalize scope gate cannot catch an accidental edit to an unrelated pending plan. The plan noted the declaration was broad but not that the fence is consequently inert for this class of mistake. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Scope check now states what the declaration costs and names the real controls (the per-file list in V-04, and small path-scoped commits), rather than implying the fence covers it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is adding an `Id` column to a child table inside this plan's scope, or a separate plan? | INSIDE scope, because no row can conform until the table resolves an id6; but INVENTING an id6 for an unauthored child is OUT and is an escalation. | Declaring the six tables a separate child (rejected: it would block the migration on six of twelve plans and split one mechanical edit across two plans, and the column addition is not a design decision). Letting the executor decide (rejected: the plan's own no-widening rule means an executor facing a refusal with no authorised fix is pushed toward widening the grammar). | child 01 E-02's refusal naming the missing column; the six tables measured; `wfjsp4`'s unauthored row and `5e4sb6`'s `03+`/`last` measured | yes |
| D-2 | Does the `CARRIER_CUTOVER_DATE` precedent support a cutover for this gate? | No. It is a severity tier and neither consumer has a severity dimension, so a cutover here is a check SKIP and must be described as one. Migrate-all is the route the evidence supports. | Treating the precedent as transferable (rejected on the measurement: `info` is the only exempt severity and `lint_text`'s disposition is binary, so there is nothing to demote into). Forbidding a cutover outright (not chosen: criterion 12 constrains the outcome, not the method, and it is E-02's decision to make with the mechanism stated honestly). | `carrier_severity_for_plan`, `_CARRIER_LEGACY_SEVERITY`, `artifact_core.drift_exit_code`, `lint_text`'s disposition rule, child 03's pre-`run_dir` siting | yes |
| D-3 | Where does the per-orchestrator disposition record live? | In THIS plan's V-04 evidence block. A one-line `## Workflow history` note on a migrated plan is permitted as a courtesy. | Writing the disposition into each migrated orchestrator (rejected: an edit beyond the authorised checklist rewrite on twelve other agents' plans). Writing nothing on the migrated plans at all (not chosen: the history line was MEASURED safe for the approval predicate and the attestation check, and it leaves a trace where a later reader of that plan looks). | `is_plan_review_approved` and `check_readiness_attestation` run against three real plans with a `migrated` line prepended; the plan's own authorisation boundary | yes |
| D-4 | Should the `V-*` side of the migration take the R1a form? | No. R1a governs the `E-*` row only; the `V-*` section keeps the schema's `V-NN validates E-NN` form and is adjusted only to preserve the bijection. | Rewriting V-items in R1a form as the Scope literally said (rejected on the measurement: `IPD-I302` plus `IPD-I303`, so it breaks every plan it touches). Leaving the Scope ambiguous (rejected: an ambiguity whose literal reading is destructive is not a tolerable ambiguity). | spec `r07vma` R1a's text (it specifies an `E-*` row); `ipd_lint.check_ids_and_bijection`; the refusal reproduced at review | yes |
| D-5 | Is E-03 still right-sized after review added four obligations to it? | Yes, `standard`, unsplit. The four are constraints on one mechanical pass over one file, verified by one `aw ipd lint` call per file. | Splitting E-03 per plan (rejected: twelve near-identical items). Splitting by concern, all tables then all rows then all watermarks (rejected on a correctness ground, not effort: it leaves every plan in a broken intermediate state between passes, and the lint that catches mistakes only passes once all of them are done for a given file). | the E-item right-sizing diagnostics applied to the revised item; the lint behaviour measured on partial edits | yes |
