# Review: surface a per-item refusal reason and its remedy in the run summary and aw runs (child r2i1b1, Set orchprobe)

- Subject-Id: r2i1b1
- Subject-Type: ipd
- Reviewed-At: 2026-09-07
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `a6954bca`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions.

DISCLOSURE: the same agent identity authored this Set earlier in the session, so this is a self-review.
Every load-bearing claim was therefore RE-MEASURED against code rather than recalled, and the blocker
below is a case where measurement contradicted what the plan asserted.

METHOD. This plan claims specific things about what two renderers do, so instead of reading them I RAN
one: `render_run_summary_table` was invoked with each of the five allowlisted statuses, carrying the
fields the host runners actually write, and the presence of a diagnostic line was recorded per status.
The `aw runs` predicate was located by an AST walk mapping every occurrence to its enclosing function,
rather than by grep, and the import graph was checked by parsing the modules.

WHAT THE PLAN GOT RIGHT, and it is the diagnosis. All three original findings are real: the diagnostics
block genuinely keys on a closed status set, `has_issue` genuinely covers only directory mismatches, and
there genuinely is no remedy field anywhere. The reasoning for WHY a remedy field must exist (a
prohibition-only message gets complied with by deletion) is the correct lesson from this repository's own
history and is the best idea in the Set. Ordering this child first, and its reason (a gate whose refusals
nobody sees is worse than no gate), are also right.

THE BLOCKER IS A FALSE PREMISE THAT WOULD HAVE BEEN FROZEN INTO A REQUIREMENT. E-02 said to keep "the
three existing special cases working verbatim (their wording is asserted by existing tests)", its
expected outcome named four statuses as unchanged, and V-02 demanded output "byte-identical to before"
for each. Measured by rendering the real function: only THREE of the five emit any line.
`integration-blocked` and `merge-conflict` emit NOTHING, because their branch is gated on
`it.get("driver_error")` while the code that sets those two statuses writes `integration_deferral`
instead (`oc_runipd.py:6498-6512`, `agy_runipd.py:3798-3811`); `driver_error` is written at exactly one
site per host (`oc_runipd.py:7204`, `agy_runipd.py:4464`), for `failed-safely`. So for those two,
"byte-identical to before" means "still renders nothing", and V-02 would have PASSED while the defect
survived. The existing test does not catch it because it supplies `driver_error` on a `failed-safely`
item (`tests/test_run_summary_table.py:198`), so the branch is exercised through the one status that
does populate the field. This is a strictly worse defect than the allowlist the plan set out to fix: an
allowlist at least reports the statuses it lists.

THE SECOND STRUCTURAL ERROR WOULD HAVE SHIPPED SURFACES THAT DISAGREE. The plan describes `has_issue` as
a single three-term expression at `run_viewer.py:1497` and E-03 extends it. Measured, that expression
appears FIVE times: `:1349` in `format_artifact_audit_summary`, `:1498` in `render_steps_table`, and
`:2564`, `:2608`, `:2639` in three `run_viewer_cli` branches serving `--json`, `--agent --issues` and
human `--issues`. Extending the one the plan names would have produced an `aw runs` table reading
`Issue: YES` while `aw runs --json` omitted the same item from `artifact_discrepancies` and `aw runs
--agent --issues` printed nothing. For a Set whose whole purpose is that a refusal not be invisible, the
machine-readable surface being the one left blind is close to the worst available outcome. Split into
E-03 (extract one predicate, prove behavior unchanged) then E-04 (extend it), because extending before
extracting is what creates the divergence.

A LATENT CIRCULAR IMPORT, which is why E-01 moved. The plan put the record in `runner_shared.py` and had
`render_stream` read it in E-02. But `runner_shared` already imports `render_stream` at module level
(`:136`, `from agent_workflows.render_stream import Palette, render_run_summary_table`), so the reverse
edge cannot exist. `render_stream` imports no first-party module at all today, which is exactly what
makes it the correct home for a type both a renderer and the runners read; E-01 now says so and V-01
requires the property be proven preserved rather than assumed.

THE REMEDY WOULD HAVE BEEN INVISIBLE BY DEFAULT. E-03 put "the reason plus remedy" in "the detail view",
but `render_step_details` is called only under `if detail:` (`run_viewer.py:1699`, `:1737`). So bare `aw
runs` would show `Issue: YES` and never say why or what to do, which is precisely the reader who most
needs the remedy. Now E-05, which also requires the fields in the machine payloads as discrete keys
rather than prose.

THE OPEN QUESTION IS A FENCE QUESTION, and I did not resolve it. Repairing the two broken statuses is
clearly right, but WHERE is a judgement about this child's boundary: fixing the renderer to also read
`integration_deferral` keeps the change inside `render_stream.py`, while making both runners additionally
set `driver_error` edits `oc_runipd.py:6498-6512` and `agy_runipd.py:3798-3811`, functions that the
`integpath` Set's approved children `51vw4y` and `rl67b0` are actively rewriting. A third option is to
declare the repair out of scope entirely and file it separately, which would shrink this child back to
its authored size. That is a scope and concurrency call, raised as OQ-02 with `- Blocking: yes`.

ON SIZE, since this review grew the plan from five E-items to eight. Every addition is a distinct
concern with its own test surface (extract, extend, place, two different guards), so the count reflects
decomposition rather than scope creep; the two additions that are genuinely NEW scope, E-04's machine
surfaces and E-02's repair half, are both consequences of measured defects the plan's own goal already
committed it to. If the maintainer takes OQ-02 option (c), E-02's repair half and its guard shrink back
out.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; E. testing; honest documentation | rendered `render_run_summary_table` per status: `dependency-blocked` True, `failed-safely` True, `integration-blocked` False, `merge-conflict` False, `interrupted` True; `render_stream.py:2138-2143`; `oc_runipd.py:6498-6512`, `:7204`; `agy_runipd.py:3798-3811`, `:4464`; `tests/test_run_summary_table.py:198` | **TWO OF THE FIVE ALLOWLISTED STATUSES RENDER NOTHING TODAY, AND THE PLAN WOULD HAVE FROZEN THAT AS A REQUIREMENT.** E-02 said keep the existing cases "verbatim", its outcome named four statuses as unchanged, and V-02 demanded byte-identical output. But the `integration-blocked`/`merge-conflict` branch gates on `driver_error`, while the code setting those statuses writes `integration_deferral`; `driver_error` is set at one site per host, for `failed-safely`. So "byte-identical to before" for those two means "still nothing", and V-02 would have PASSED on a live defect. The existing test misses it because it supplies `driver_error` on a `failed-safely` item. This is worse than the allowlist the plan targets: an allowlist at least reports what it lists | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 rewritten: preserve verbatim ONLY the three that work (naming the asserting lines `:211-214`), and REPAIR the two that render nothing. V-02 now requires the before/after contrast rendered with `integration_deferral` rather than `driver_error`, with the before showing NO line. New F-4; the Concern paragraph states it. New E-07/V-07 guard the defect CLASS (a branch reading a field no producer writes) with a mutation check that must reproduce this exact failure. Fence question raised as OQ-02 |
| PR-002 | BLOCKER | UNDER-SCOPE | A. correctness; C. architecture; E. testing | AST walk mapping each occurrence to its enclosing function: `run_viewer.py:1349` (`format_artifact_audit_summary`), `:1498` (`render_steps_table`), `:2564`/`:2608`/`:2639` (`run_viewer_cli`) | **THE ISSUE PREDICATE IS FIVE COPIES, NOT ONE, SO THE PLAN WOULD HAVE SHIPPED SURFACES THAT DISAGREE.** The plan describes it as a single expression at `:1497` and extends that. The other four serve the artifact-discrepancy summary, `--json`, `--agent --issues` and human `--issues`. Extending one gives an `aw runs` table reading `Issue: YES` while `--json` omits the same item and `--agent --issues` prints nothing. For a Set whose purpose is that a refusal not be invisible, leaving the MACHINE-READABLE surface blind is close to the worst outcome available | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Split into E-03 (EXTRACT one predicate, route all five call sites through it, prove behavior unchanged by suite not inspection) and E-04 (EXTEND it so a refusal counts). Extraction precedes extension deliberately, since extending first is what creates the divergence. V-03 requires proof all five sites call it and that no sixth copy remains; V-04 requires all five surfaces agreeing on a refused run AND on a clean run. New F-2 rewritten with all five locations; Scope declares the machine surfaces |
| PR-003 | HIGH | IN-SCOPE | C. architecture | `runner_shared.py:136`; AST check that `render_stream` imports only stdlib | **THE RECORD'S HOME WAS A CIRCULAR IMPORT.** E-01 put it in `runner_shared.py` and E-02 had `render_stream` read it, but `runner_shared` already imports `render_stream` at module level, so the reverse edge cannot exist. The executor would have discovered this only on the first import error, mid-implementation, with the plan telling it to do the impossible thing | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 re-sited to `render_stream.py` WITH the mechanical reason and the measured import direction, noting that `render_stream` imports no first-party module today and that relocating `render_run_summary_table`'s import would be a different change (listed in Deferred). V-01 now requires proof the property is preserved (an AST walk plus a fresh-interpreter import). E-08 requires importing from `render_stream`, never from the other host's driver |
| PR-004 | MEDIUM | UNDER-SCOPE | F. UX; self-documentation | `run_viewer.py:1537`, `:1699`, `:1737` | **THE REMEDY WOULD HAVE BEEN INVISIBLE WITHOUT A FLAG.** E-03 placed "the reason plus remedy" in the detail view, but `render_step_details` runs only under `if detail:`. Bare `aw runs` would show `Issue: YES` and say neither why nor what to do, and that reader is exactly the one the remedy exists for | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | New E-05 requires the remedy visible with NO flag (choosing and recording the default location), the full reason under `--detail`, and code/reason/remedy as DISCRETE fields in `--json`/`--agent`. V-05 requires all four pasted. New F-5 |
| PR-005 | HIGH | IN-SCOPE | Scope fence; C. operability (concurrency) | `oc_runipd.py:6498-6512`; `agy_runipd.py:3798-3811`; `.aw/records/plans/pending/` `51vw4y` and `rl67b0` both `Status: approved` over those functions | **THE REPAIR PR-001 REQUIRES MAY OR MAY NOT BE THIS CHILD'S TO MAKE, AND THE PLAN'S SCOPE CANNOT ANSWER IT.** The field mismatch spans a renderer and two runners: fixing the renderer to also read `integration_deferral` stays inside `render_stream.py`, while making both runners additionally set `driver_error` edits functions that two APPROVED `integpath` children are actively rewriting, risking a conflict for no behavioral gain. A third option is to declare the repair out of scope and file it separately, shrinking this child back to its authored size | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | Escalated as OQ-02 with `- Blocking: yes` and `- Finding: PR-005`, owner maintainer, three costed options (renderer-side, both-runners, or out-of-scope-and-filed) with (a) recommended and the concurrency risk named. The gate states execution is blocked on it and that approval alone does not clear it. NOT FIXED because a fence boundary and a concurrency trade-off are the maintainer's call |
| PR-006 | HIGH | IN-SCOPE | E. testing; honest documentation | measured `python3 -m pytest` bare: `1 failed, 5632 passed, 3 skipped, 2 xfailed`; `python3 -m pytest tests/test_run_viewer.py`: `46 passed`; failing node id `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` | **THE BASELINE CONVENTION WAS STALE AND FALSE, IN THE DANGEROUS DIRECTION, ON A MODULE THIS CHILD EDITS.** It told the executor to expect "~14 `test_run_viewer` failures ... the known `agrlvw` live-repo fixture". Measured: that module is `46 passed`, zero failures. So a real regression introduced by E-03/E-04/E-05, all of which edit `run_viewer.py`, would have been dismissed as pre-existing. The one real failure is elsewhere and is a live-repo status coupling | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Convention replaced with the measured numbers, the HEAD, the exact failing node id and its cause, and the instruction to re-measure in the executing worktree comparing node ids. Deferred's `agrlvw` bullet removed as premised on the false claim |
| PR-007 | LOW | IN-SCOPE | Evidence accuracy | AST walk over `agy_runipd`'s `ImportFrom` nodes targeting `oc_runipd`: 47; backlog `cnwy8g` records 40 | The plan cites "~46 names"; the measured count is 47, and the backlog item it cites recorded 40, so the coupling has grown since that item was filed. A "~" figure is not a baseline a V-item can check against | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 states 47 with the measurement method and date and notes the growth since `cnwy8g`; V-08 requires the before/after count showing it did not increase from 47. New F-6 |
| PR-008 | MEDIUM | IN-SCOPE | G. executability (scope fence) | pre-revision `Scope-Paths`; `tests/test_run_summary_table.py:179-214`; `ls tests/test_run_order_announcement.py` versus the plan's Scope check | **THE FENCE NAMED A FILE THE PLAN NEVER EDITS AND OMITTED THE ONE IT MUST.** `Scope-Paths` declared `tests/test_run_order_announcement.py` (whose Scope check then says not to refactor it), while omitting `tests/test_run_summary_table.py`, which holds the diagnostics-wording assertions E-02 must extend. Under `aw ipd finalize`'s scope gate the executor would owe a `--scope-ack` for a file it had no reason to touch and a `--scope-reason` for the file it necessarily did. The two runner modules E-02's repair half needs were also absent | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `Scope-Paths` corrected: `test_run_order_announcement.py` dropped, `tests/test_run_summary_table.py` added, `oc_runipd.py` and `agy_runipd.py` added with the Scope check narrowing them to E-01's import and E-02's repair only, and naming the concurrent `integpath` work. Required tests section now says to EXTEND `:179-214` rather than rewrite it |
| PR-009 | LOW | IN-SCOPE | A. correctness; D. anti-regression | pre-revision OQ-01; `tests/test_run_summary_table.py:211-214`; `oc_runipd.py:345`, `:3183-3185` | **AN OPEN QUESTION LICENSED TOUCHING ASSERTED STRINGS WITHOUT SAYING WHICH.** OQ-01 told the executor a remedy on `dependency-blocked` "must NOT" be done if it means rewriting asserted strings, but named neither the strings nor the file, so the executor would have had to rediscover the constraint. It also did not mention that the recovery text already EXISTS per host (`DEPENDENCY_BLOCK_RECOVERY_HINT`) and is already rendered in the report, so the work is plumbing rather than composition | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 narrowed: names the asserting lines as untouchable, permits only an additional line or field, cites the existing per-host hint and its current render site so the executor does not compose new text, requires recording a refusal to do it, and states that the two statuses E-02 repairs are NOT covered by this question since they assert nothing today |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where must the shared refusal record live, given the plan says `runner_shared` but `render_stream` has to read it? | `render_stream.py` | `runner_shared.py` as authored, rejected because it is a circular import: `runner_shared` already imports `render_stream` at module level, so the reverse edge cannot exist. Moving `render_run_summary_table`'s import out of `runner_shared` first, rejected as a separate change with its own risk, and recorded in Deferred rather than smuggled in | `runner_shared.py:136`; AST check that `render_stream` imports only stdlib | yes |
| D-2 | Extend the issue predicate in place, or extract it first? | EXTRACT first (E-03), then extend (E-04) | Extend the one copy the plan names, rejected on measurement: there are five copies across three functions, so extending one leaves the table saying YES while `--json`, `--agent --issues` and human `--issues` disagree, which for this Set is the worst surface to leave blind. Extend all five in place without extracting, rejected because it institutionalizes the duplication that caused the defect | AST walk locating `run_viewer.py:1349`, `:1498`, `:2564`, `:2608`, `:2639` and their enclosing functions | yes |
| D-3 | Should V-02 keep demanding byte-identical output for all the existing special cases? | NO. Byte-identical for the THREE that work; a before/after CONTRAST for the two that render nothing | Keep the blanket byte-identical requirement, rejected because for `integration-blocked` and `merge-conflict` "identical to before" means "still nothing", so the V-item would have passed on the defect it was supposed to guard. Drop the byte-identical requirement entirely, rejected because three statuses have exactly-asserted strings that a rewrite would break | rendered per-status measurement (3 of 5 emit a line); `render_stream.py:2138-2143` versus `oc_runipd.py:6498-6512` and `agy_runipd.py:3798-3811`; `tests/test_run_summary_table.py:198`, `:211-214` | yes |
| D-4 | Is the remedy's placement in the detail view sufficient? | NO. Require it visible with no flag, plus the full reason under `--detail`, plus discrete fields in the machine payloads | Leave it detail-only as authored, rejected because `render_step_details` is gated on `if detail:`, so the default reader sees `Issue: YES` with no why and no what-next, which defeats the remedy's stated purpose | `run_viewer.py:1537`, `:1699`, `:1737` | yes |
| D-5 | Escalate the repair-fence question, or decide it? | ESCALATE as OQ-02 `Blocking: yes`, readiness NO-GO, with (a) renderer-side recommended | Decide (a) myself, rejected because although it is the smaller change, the choice also determines whether this child touches two runner modules that two APPROVED plans are concurrently rewriting, and a concurrency trade-off plus a fence boundary are the maintainer's call. Decide (c) out-of-scope myself, rejected because it would leave a measured defect unfixed by a plan that had just documented it | `oc_runipd.py:6498-6512`; `agy_runipd.py:3798-3811`; `51vw4y` and `rl67b0` both `- Status: approved` over those functions; ESCALATED in-plan as OQ-02 with `- Finding: PR-005`, and maintainer told 2026-09-07 in this review's final report | no |
| D-6 | Add a second guard (E-07) for the field-mismatch class, when E-06 already guards the allowlist? | YES, add it | Rely on E-06 alone, rejected because the two guard different things: E-06 catches a closed status set returning, while the defect actually found was a branch whose CONDITION reads a field no producer writes, which an allowlist guard cannot see. That defect survived a green suite for as long as it has existed, which is the argument for guarding it explicitly | rendered per-status measurement; `tests/test_run_summary_table.py:198` supplying `driver_error` on a `failed-safely` item, which is why the branch looks exercised | yes |
