# Review findings: plan 5o1jye

- Subject-Id: 5o1jye
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `04352120` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`); `--phase review-finalize --json` conforms
after revision with zero diagnostics (one `IPD-Z602` info on E-01 appeared mid-revision and was
cleared by splitting that item's prose into paragraphs). No pre-review snapshot was owed: the plan
was committed and unmodified (`git status --short` showed no entry for it), and the lane-input copy
under `.aw/state/lane-inputs/rev-14/` is the same content.

BOTH DEFECTS THE PLAN NAMES REPRODUCE EXACTLY, and the plan's central judgement is right. Rendering
the described queue through the real `render_stream.render_run_summary_table` with `Palette(False)`
printed `• eee555: dependency-blocked (executed:aaa111 (target reviewed) (blocked))` for the legacy
token and `<<< NO DIAGNOSTIC LINES AT ALL >>>` for the canonical `fail-depend`; the real
`runner_shared.write_report` printed a correct `## Dependency blocks (why)` section under the legacy
token and omitted it entirely under the canonical one. F-04's attribution to `6b94a4d9` is verbatim
(three tuples widened, the diagnostics equality untouched). F-05's history is exact
(`git log --diff-filter=D` returns `19313eed`; `git merge-base --is-ancestor 19313eed 6b94a4d9`
confirms the guard deletion preceded the break by one day). F-06's coverage census reproduces, and
F-10's blast-radius bound holds (no existing test asserts on the token TEXT). Its decision to fix the
producer AND both renderers is correct for the reason F-07 gives.

WHAT REVIEW FOUND IS THAT THE PLAN OVERSTATES WHAT THREE OF ITS FOUR CODE EDITS ACHIEVE, in ways that
would each have misdirected the executor, and that a THIRD producer of the key pair was never counted.

**E-03 IS A NO-OP FOR THE SHAPE THE PLAN AIMS IT AT, AND ITS MUTATION CHECK COULD NOT GO RED
(PR-101, HIGH).** Once E-01 writes a bare token plus a reason map, the placeholder
`reasons.get(d, 'blocked')` is never consulted for a cascade item, because the key is present.
Measured: both the fixed and the placeholder composition over the post-E-01 shape yield
`executed:aaa111 (target aaa111 is reviewed)`, byte-identical. So V-05(i) as authored - "restore the
placeholder and show the double-explain case FAIL" - would have shown the case still PASSING if the
executor built it from the cascade, which is exactly what E-05(a) tells them to do. An executor facing
a mutation that will not go red either weakens the test or concludes the edit was unnecessary. E-03 is
nonetheless required, on a narrower basis the plan did not state: the embedded-reason-no-map shape
survives in every run directory frozen by today's driver, and the renderer is what those are read back
through. E-03, E-05(b) and V-05(i) now name the frozen-record shape as the subject, and V-03 requires
the two compositions be printed side by side so the no-op is recorded rather than re-discovered.

**"SHAPE-IDENTICAL TO THE DRAIN PATH" IS NOT WHAT E-01 DELIVERS (PR-102, MEDIUM).** The drain arms
also write `item["dependency_block_recovery"]` and four extra event keys (`reasons`, `recovery`,
`block_class`, `block_detail`). Worse for a parity claim, `oc_runipd.DEPENDENCY_BLOCK_RECOVERY_HINT !=
agy_runipd.DEPENDENCY_BLOCK_RECOVERY_HINT` (measured; each names its own host's resume command), so
there is no single value the shared cascade could adopt without inventing host-neutral wording this
plan has no mandate for. Left uncorrected, a later reader would cite this plan as having unified the
shapes that backlog `mjrac4` still tracks. E-01 now states two-KEY parity and forbids the third key
explicitly; V-01 requires `dependency_block_recovery` be printed as `None`.

**A THIRD PRODUCER EXISTS AND E-04 REVIVES ONLY ONE OF ITS TWO SURFACES (PR-103, MEDIUM).**
`dispatch_orchestrator_item` writes the same key pair from `decision.unfinished`, writes
`terminal_status` (default `fail-depend`), AND records a `Refusal`. Measured on such an item: the
summary table renders `• orc999: fail-depend (r)` from the `elif refusal is not None` branch, which
precedes the dependency arm, so its per-child reasons never appear there and will not after E-03/E-04
either; the report section is absent under `fail-depend` and correct under the legacy token. So E-04's
report half is what restores the `5e4sb6` guarantee for this producer. Added as F-15 and OQ-03, pinned
by a new E-05(f), with V-04 requiring the executor state plainly that the table shows only the refusal
line, since the opposite claim would be false.

**E-02's TWO CONSTRAINTS WERE ONE CONSTRAINT AND A WRONG PREMISE (PR-104, MEDIUM).** OQ-01 said
`dependency_status_detailed` "distinguishes an out-of-queue target ('not in this run') from an in-run
one". It does not: measured with the target PRESENT in `state["queue"]`, its reason contains that
phrase and `derive_item_disposition` returns `dependency_not_met_external`. That makes the prohibition
on the cascade emitting the phrase more important, not less. Review also found a constraint the plan
missed entirely: the drain path's strings are TOKEN-PREFIXED (`edge_satisfied` composes `f"{tok}:
..."`), so matching them literally would make the renderer print the token twice. Both are now
requirements on E-02 with printed-boolean evidence demanded in V-02.

**E-04's JUSTIFICATION CITED A GUARD THAT DOES NOT EXIST (PR-105, MEDIUM).** It said a runner import
into `render_stream` is forbidden by "its import-purity guards"; `tests/test_orchestrator_probe_cache.py`
is absent at HEAD and no test anywhere pins that module's import surface. The real reason is stronger
and durable: `runner_shared` imports `render_stream` at MODULE LEVEL, so the reverse edge is an import
cycle. Corrected in E-04 with the `zyw4n3` comment that records the direction as forced.

**TWO ADJACENT DEFECTS MEASURED AND FILED RATHER THAN ABSORBED (PR-201, PR-202).** `8mohre` (`bug`,
`Blocks-Release: next`): `derive_item_disposition` labels an in-queue unmet dependency
`dependency_not_met_external` with the gloss "outside this run's queue", inverting the distinction its
own comment calls actionable. `csjq81` (`chore`): every drain reason prints its token twice. Both sit
outside this plan's fence (the first needs `run_selection_policy.py` and a standing maintainer ruling
about `edge_satisfied`'s `by_id`; the second would change strings that durable run records and a
substring-matched code selector read), and both now have Deferred rows naming their carriers.

**THE GATE DID NOT DECLARE ITS OWN NEAR-MISS EDITS (PR-301, LOW).** Two of the most tempting wrong
edits are in files the executor is already touching or reading (`edge_satisfied` is in the plan's own
`runner_shared.py`). Added an explicit two-file prohibition with the reason for each.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. No open question blocks: OQ-01 and OQ-02 were resolved by the author from evidence and both
survive review with corrections recorded; OQ-03 is new and resolved from measurement.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | D. Anti-regression / E. Testing | plan E-03, E-05, V-05(i); `render_stream.render_run_summary_table`'s `reasons.get(d, 'blocked')` arm | E-03 CHANGES NOTHING for the shape the plan aims it at, and its mutation check therefore cannot go red. After E-01 the reason map is present, so the placeholder is never consulted: both compositions over `deps=['executed:aaa111']`, `reasons={'executed:aaa111': 'target aaa111 is reviewed'}` yield `executed:aaa111 (target aaa111 is reviewed)`, byte-identical. V-05(i) told the executor to restore the placeholder and watch the double-explain case fail; built from the cascade item E-05(a) mandates, it would have PASSED. The edit is still required, for frozen run records carrying the embedded-reason-no-map shape. | C:Low; U:Low; S:Low; F:Low; Overall:Low (a re-aimed test subject and a corrected claim; no code design changes) | FIXED | Added F-10a with both measurements. E-03 now states it is a FROZEN-RECORD repair and forbids claiming it fixes live cascade output. E-05(b) names the frozen shape as its subject. V-03 requires the two compositions be printed side by side. V-05(i) names the frozen-record case as the mutation's subject and explicitly forbids using the post-E-01 cascade item, and adds "if any mutation will not go red, say so and fix the TEST". |
| PR-102 | MEDIUM | IN-SCOPE | A. Correctness / G. Plan executability | plan E-01 ("shape-identical to the drain path's"); `oc_runipd`/`agy_runipd` drain arms; `DEPENDENCY_BLOCK_RECOVERY_HINT` in both hosts | THE PARITY CLAIM IS FALSE AND UNREACHABLE. The drain path also writes `item["dependency_block_recovery"]` plus `reasons`/`recovery`/`block_class`/`block_detail` on the event, and the recovery hint is NOT one object: the two hosts' constants differ (each names its own resume command), so a shared cascade cannot adopt one without inventing host-neutral wording. An executor reading "shape-identical" could add the third key with one host's wording, or a later reader could cite this plan as closing `mjrac4`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with the measured constant inequality. E-01 now says two-KEY parity, forbids `dependency_block_recovery` and the four event keys by name, and states the claim that may be made afterwards. V-01 requires `dependency_block_recovery` printed as `None`. `mjrac4` named as the carrier for full unification. Scope and Proposed-changes lines corrected. |
| PR-103 | MEDIUM | UNDER-SCOPE | A. Correctness / E. Testing | `runner_shared.dispatch_orchestrator_item` (writes the key pair and a `Refusal`); `render_stream.render_run_summary_table`'s `elif refusal is not None` branch preceding the dependency arm | A THIRD PRODUCER OF THIS KEY PAIR WAS NEVER COUNTED, and for it E-04 revives only ONE of the two surfaces. Measured on an orchestrator-TERMINATE item: the summary table prints `• orc999: fail-depend (r)` from the refusal branch and never reaches the dependency arm, so its per-child reasons appear there neither before nor after this plan; the report section is absent under `fail-depend` and correct under the legacy token. So E-04's report half is what restores the `5e4sb6` guarantee here, and an unqualified claim that the table now shows unfinished children would be false. Untested, this producer could also regress unnoticed. | C:Low; U:Low; S:Low; F:Medium (an untested third producer of the key E-01 reshapes); Overall:Medium | FIXED | Added F-15 with the probe output. Added OQ-03 resolved from that measurement. Added E-05(f) pinning the orchestrator case's report section. V-04 now requires the orchestrator probe under both spellings and an explicit one-sentence statement that the table shows only the refusal line. |
| PR-104 | MEDIUM | IN-SCOPE | A. Correctness / F. Principles | plan OQ-01; `run_selection_policy.derive_item_disposition`'s `if "not in this run" in named`; `edge_satisfied`'s `f"{tok}: ..."` refusal composition | OQ-01 RESTS ON A FALSE PREMISE AND MISSES A SECOND CONSTRAINT. It says `dependency_status_detailed` distinguishes an out-of-queue target by the phrase `not in this run`; measured with the target PRESENT in the queue, the reason carries that phrase and `derive_item_disposition` returns `dependency_not_met_external`. Separately, every drain reason is TOKEN-PREFIXED, so prose matching the drain path literally would make the renderer print the token twice. E-02 as authored required only "consistency of register", which neither constraint follows from. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11 and F-12 with measured output. E-02 now carries both prohibitions as explicit requirements (no `not in this run`, no token prefix) with the reason for each. V-02 demands each as a printed boolean over the actual string. OQ-01's rationale corrected in place, labelled as corrected, and pointed at the two new carriers. |
| PR-105 | MEDIUM | IN-SCOPE | C. Architecture | plan E-04 ("import-purity guards forbid"); `runner_shared.py`'s module-level `from agent_workflows.render_stream import (...)`; absent `tests/test_orchestrator_probe_cache.py` | THE STATED REASON FOR NOT IMPORTING A RUNNER INTO `render_stream` CITES A GUARD THAT DOES NOT EXIST. The named test file is absent at HEAD and no test pins that module's import surface, so an executor verifying the constraint would find nothing and might conclude the import is permitted. The real constraint is stronger: `runner_shared` imports `render_stream` at module level, so the reverse edge is an import CYCLE, and `runghostid` `zyw4n3` records the direction as FORCED. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14. E-04 now distinguishes the two modules explicitly (`canonical_terminal_status` in `runner_shared`, which needs no import; local both-token comparison in `render_stream`) and gives the cycle as the reason. V-04 requires the import list be pasted and still be exactly `lifecycle_style` and `term`. |
| PR-106 | LOW | UNDER-SCOPE | A. Correctness / G. Plan executability | `runner_shared.dispatch_orchestrator_item`'s comment "it is gated on `status == \"dependency-blocked\"`, which is `terminal_status`'s default"; that parameter's default `fail-depend` | A COMMENT IN THE PLAN'S OWN FILE ASSERTS THE COUPLING E-04 REPAIRS, and is false today. The plan quotes it in F-03 as evidence of the defect but assigns no item to correct it, so the fix would land beside a comment telling the next reader the gate keys on the retired token. That is the stale-citation class this repository repeatedly pays for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now carries the comment correction with its rationale, its Expected outcome requires the comment no longer assert the retired coupling, and V-04 requires the corrected text be quoted. |
| PR-201 | MEDIUM | OVER-SCOPE | A. Correctness (adjacent defect, excluded) | `run_selection_policy.derive_item_disposition`; probe with the target in `state["queue"]` returning `code='dependency_not_met_external'` | AN IN-QUEUE DEPENDENCY IS ALREADY MISLABELLED EXTERNAL, on a surface this plan does not declare. `edge_satisfied` resolves `executed:` edges on disk (by maintainer ruling it deliberately ignores `by_id`) and words every on-disk refusal as an external-target refusal, so the substring selector picks the EXTERNAL code for a queue member, with the gloss "outside this run's queue". The distinction is the one that function's own comment calls actionable. Fixing it needs an undeclared module and a typed signal, and must not reintroduce a queue-status read into the satisfaction decision. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium (an undeclared module plus a standing ruling) | FIXED | FILED AND FENCED (this plan is the wrong carrier; nothing is left unowned). Filed as backlog `8mohre` (`bug`, `Blocks-Release: next`) with the measurement and the fix direction including the ruling's constraint. Recorded as plan F-12, given a Deferred row with `Carrier: 8mohre`, and named in the gate's do-not-edit list. E-02's prohibition prevents this plan adding a third route to the same mislabel. |
| PR-202 | LOW | OVER-SCOPE | F. UX (adjacent defect, excluded) | `edge_satisfied`'s `f"{tok}: ..."`; rendered line `• eee555: dependency-blocked (executed:5o1jye (executed:5o1jye: external target ...))` | THE DIAGNOSTICS LINE PRINTS THE DEPENDENCY TOKEN TWICE for every drain item, because the reason strings already begin with it. Verbose but internally consistent (one authoritative reason), so it is not this plan's defect; fixing it would change strings read by `derive_item_disposition`'s substring selector, by `write_report`, and by durable `events.jsonl` records. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FILED AND FENCED (this plan is the wrong carrier; nothing is left unowned). Filed as backlog `csjq81` (`chore`) with the measurement, the four readers, and a fix direction that keeps durable records byte-identical. Recorded as plan F-11 with a Deferred row carrying `Carrier: csjq81`, and named in the gate's do-not-edit list so the executor does not strip the prefix in the file they are already editing. |
| PR-301 | LOW | UNDER-SCOPE | G. Plan executability | plan gate (execution contract) | THE GATE NAMED NO FORBIDDEN NEIGHBOURS, and both near-miss edits this review measured are within easy reach: one is in the plan's OWN declared file (`edge_satisfied`), the other in the module the plan copies its repair FROM. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a two-file prohibition paragraph to the gate naming `run_selection_policy.py` and the `edge_satisfied` reason strings, each with its reason and carrier. |
| PR-302 | LOW | IN-SCOPE | E. Testing | plan E-05; `write_report`'s `item['setid']` subscript; `dependency_status_detailed`'s `state["repo"]` read | TWO SETUP REQUIREMENTS THE NEW TEST MODULE WILL HIT IMMEDIATELY were undocumented: `write_report` raises `KeyError: 'setid'` on an entry lacking `setid`/`position`, and `dependency_status_detailed` raises `KeyError: 'repo'` without `state["repo"]`. Both cost the executor a discovery round trip. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now names both requirements, and directs the drain case to derive its map by CALLING `dependency_status_detailed` rather than hand-writing reason prose, so the test cannot pass against a changed reason vocabulary. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03 is a no-op for the post-E-01 cascade shape. Drop the item as unnecessary, or keep it on a narrower basis? | KEEP IT, restated as a FROZEN-RECORD repair, and re-aim its mutation check at the embedded-reason-no-map shape. | (a) Drop E-03 - rejected: run directories frozen by today's driver carry the embedded-reason shape with no map, and the renderer is what they are read back through, so dropping it leaves the reported defect live for every historical record. (b) Keep it as authored - rejected: V-05(i) could not go red, and a mutation that cannot fail is not evidence by this repository's own standard. (c) Also migrate frozen records - rejected: mutating durable history, which the plan's own Deferred section already forbids. | Measured: both compositions over the post-E-01 shape are byte-identical, and differ only on the frozen shape (`executed:aaa111 (target reviewed)` versus `... (blocked)`). The both-tokens acceptance in E-04 rests on the same frozen-record premise, so the plan is already committed to it. | yes |
| D-2 | `dispatch_orchestrator_item` is a third producer whose summary-table line is swallowed by the refusal branch. Widen the plan to surface it there, or bound the claim? | BOUND THE CLAIM: E-04 revives the written report for that producer, the table keeps showing its refusal line, and E-05(f) pins the report case. | (a) Reorder the renderer so the dependency arm precedes the refusal branch - rejected: the refusal-first ordering is `r2i1b1` E-02's deliberate design (a typed refusal record is strictly more informative than a status-keyed legacy field), and reversing it would change the line for every refusing status, far outside this fence. (b) Render both - rejected: two lines per item is a presentation change to a surface no finding shows to be defective. (c) Say nothing - rejected: the plan would then imply E-04 restores both surfaces for all producers. | `dispatch_orchestrator_item` writes the pair from `decision.unfinished` and calls `record_refusal`; measured, the table printed only `• orc999: fail-depend (r)` while the report under the legacy token printed the per-child reason. The `5e4sb6` guarantee E-04 restores is a REPORT guarantee. | yes |
| D-3 | The in-queue `dependency_not_met_external` mislabel is a real `bug` gating `next`. Fix it in this plan or file it? | FILE IT as backlog `8mohre` and fence this plan against it. | (a) Fix here - rejected: it needs `run_selection_policy.py`, which this plan does not declare, and a correct fix must not reintroduce a queue-status read into `edge_satisfied`'s satisfaction decision (standing maintainer ruling of 2026-09-19), so it carries a design decision of its own. (b) Fold into `mjrac4` - rejected: `mjrac4` is the SHAPE divergence and is `chore`; this is a false operator-facing statement and is `bug`, so merging them would bury a release-gating defect under a low-priority cleanup. (c) Leave it in plan prose only - rejected: prose is invisible to `aw attention`. | Probe with the target in the queue returned `code='dependency_not_met_external'`; `derive_item_disposition`'s own comment states the distinction is actionable; `edge_satisfied`'s docstring records the `by_id` ruling. Repository policy: a live `bug` carries `Blocks-Release`. | yes |
| D-4 | Should E-02 require the cascade's prose to match the drain path's wording more closely, given OQ-01's premise was wrong? | NO: keep register-consistency, and ADD two hard prohibitions (no `not in this run`, no token prefix). | (a) Route the cascade through `dependency_status_detailed` for byte-identical strings - rejected: that predicate reads the DISK and `state["repo"]`, gates on findings, and is a satisfaction predicate; calling it from the cascade changes a gating function's call graph for a wording benefit. (b) Leave E-02 at "consistency of register" - rejected: neither prohibition follows from that phrasing, and F-12 shows one of them now guards a live defect. | Measured drain string is token-prefixed and contains `not in this run` for an in-queue target; `derive_item_disposition` selects its EXTERNAL code on that substring; the cascade has the target's status in hand and needs no disk read. | yes |
