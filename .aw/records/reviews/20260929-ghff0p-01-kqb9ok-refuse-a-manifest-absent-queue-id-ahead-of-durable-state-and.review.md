# Review findings: plan kqb9ok

- Subject-Id: kqb9ok
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `639c877a` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED before revision (exit 0, `findings: 0`); `--phase review-finalize` conforms after revision with
all five `E-*`/`V-*` pairs. No pre-review snapshot was owed: the plan was committed and unmodified at
review start, and the lane-input copy under `.aw/state/lane-inputs/rev-18/` is byte-identical to the
tracked plan. Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 62.95s`. NO PRODUCTION
FILE OR TEST WAS MODIFIED by this review; measurements ran against a purpose-built fixture repository under
`.aw/state/runtime/`, deleted afterwards.

THE PLAN'S CENTRAL JUDGEMENT IS RIGHT AND ITS HONESTY IS ITS BEST FEATURE. It was authored from a backlog
item, discovered on re-measurement that the item's primary defect no longer exists, and rather than
manufacturing a fix it retracted the premise and narrowed to measured residue. I verified both halves of
that judgement rather than accepting it.

F-01 CONFIRMS ON BOTH CLAUSES. The unguarded access is gone: `lookup_manifest_artifact` guards every map
with an `in` test and ends `raise DriverError(f"No manifest entry found for artifact '{id6}'")`, so no bare
`KeyError` escapes. The re-siting also confirms: in `initialize_run_core` the queue loop (`for position,
id6 in enumerate(queue_ids, start=1)` followed immediately by `lookup_manifest_artifact`) precedes `run_id =
getattr(args, "run_id", None) or new_run_id()` and `run_dir = state_root(repo) / run_id`, with
`enforce_freeze_time_refusal` and `enforce_orchestrator_shape_gate` between them, exactly as F-01 describes.

F-02 CONFIRMS AND IS A REAL, LIVE DEFECT, which is the finding that justifies E-02 existing at all. On a
fixture holding a conformant IPD at `docs/20260927-s2-01-pln002-outside.ipd.md` with a matching manifest
entry: `resolve_plan_path` raises `Refusing 'docs/20260927-s2-01-pln002-outside.ipd.md' for IPD pln002: it
is outside the plans trees, not an IPD plan`; `resolve_selected_artifact_paths(repo, manifest, ["pln002"])`
returns `TypedSelection(plan_paths=(), all_paths=(), unresolved=('pln002',))`, matching F-02's measurement
exactly; `enforce_freeze_time_refusal` PASSES the entry with no refusal (its structure check tests only
`abs_path.is_file()`, which a `docs/` file satisfies); and `queue_plan_path_for` on that same entry then
raises the refusal. So the pre-queue gate admits it and the refusal arrives at dispatch, which is the
post-durable-state property the item was filed to protect.

F-03, F-04, F-05 AND F-06 ALL CONFIRM. `No manifest entry found` and `lookup_manifest_artifact` each grep
to zero hits under `tests/`. `.unresolved` has exactly one repository reader, the assertion in
`tests/test_typed_queue_entries.py`; the only `agent_workflows` hit is the unrelated
`unresolved_blockers`. All three stale comments are present verbatim at `match_spec_selector`,
`closure_target_admission` and `enforce_mixed_type_gate`, and F-05's assessment of the third is precisely
right: `resolve_selected_artifact_paths` does still contain `except (DriverError, KeyError): resolved =
None`, so that comment's ARGUMENT survives while its quoted code moved. `run_selection_policy.py` still
carries `offset 70` and `offset 134`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | A (correctness) / D (anti-regression) | plan E-02; `agent_workflows/runner_shared.py` `action_for`, `success_states_for_action`, `enforce_freeze_time_refusal` | E-02 said "refuse any IPD queue entry whose configured `file` cannot be resolved", with NO action scoping, so it would refuse a whole run over a misfiled path on an entry that is never dispatched. Measured: `action_for` returns `skip` for status `executed`/`superseded`/`not-executed` and `undetermined` for `draft`; a `skip` never reaches `queue_plan_path_for` and `success_states_for_action` treats a completed skip as a SUCCESS. That is a run which succeeds today and would refuse after E-02. The plan's own gate even anticipates the class of error ("a gate that refuses live work is a worse defect than the one being fixed") without scoping the item to prevent it | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now requires the refusal be gated on the live-action set, following `enforce_freeze_time_refusal`'s own precedent (`not is_in_terminal_directory(...)` then `action in ("review", "execute", "orchestrate")`) rather than a new predicate. E-03 gains the NEGATIVE case (same misfiled path on a `skip` entry must NOT refuse) and V-02 now requires the predicate be stated verbatim and the negative measurement pasted, so an unscoped implementation cannot pass. New F-09 records the measurement |
| PR-202 | MEDIUM | IN-SCOPE | G (plan executability) | plan E-02 / Proposed change 2; the queue loop's `resolve_plan_path` and `action_for` calls | The action PR-201 requires scoping on is computed LATER in the same loop body than the `resolve_plan_path` call whose error must be captured, so a naive implementation of the scoped refusal cannot raise where it detects. The plan gave no ordering guidance, leaving an executor to discover the constraint mid-change and possibly to resolve it by re-siting the resolver call (extra filesystem work) or by refusing unscoped (PR-201) | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | E-02's Proposed change now states the constraint explicitly and directs the executor to COLLECT the resolver error and decide once the action is known. New F-10 records the ordering |
| PR-203 | MEDIUM | IN-SCOPE | G / internal consistency | plan `## Scope check` under-scope bullet | The bullet asserted E-02 and E-03 "can be dropped without affecting the rest" and, in the SAME sentence, that "E-04's rewrite depends on E-02's outcome being true". Both cannot hold, and E-04/E-05 do declare `Depends on: E-02`/`E-04`. A maintainer answering OQ-01 on the cheaper reading would have been told the drop was free when it is not | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bullet now itemizes the real coupling: exactly ONE clause of E-04 is contingent (`enforce_mixed_type_gate`'s forward warning, which must say the drop-and-continue behavior SURVIVES if E-02 is dropped), everything else is independent, so the drop costs one re-worded clause and the executor must re-word it rather than leave a comment crediting a refusal the run does not perform |
| PR-204 | MEDIUM | UNDER-SCOPE | G / release-gate integrity | plan OQ-01; `- Blocks-Release: next`; backlog `ghff0p` | OQ-01 offers the maintainer a path that drops E-02/E-03, but the plan carries `Blocks-Release: next` inherited from a `Work-Kind: bug` item, and F-02 is a CONFIRMED live defect. On the drop path nothing obliged anyone to file F-02, so the release blocker would be silently lost. The gate's drop instructions were also incomplete on two further points: they told the executor to mark dropped items "deferred", which is not a legal execution state, and said nothing about the resulting unfinalizability | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | OQ-01 now states that if E-02/E-03 are dropped, F-02 MUST be filed with `aw backlog new` carrying the gate forward. The gate enumerates three owed acts on that path (record and mark with legal states, re-word E-04's clause, file F-02), names `blocked` as the legal state with its required `Execution note:`, and states the `pre-transition` consequence so the executor does not discover it at finalize |
| PR-205 | LOW | IN-SCOPE | G / Step 4 | plan gate, transition paragraph | No conditional runner/executor ownership of `aw ipd finalize`, and no instruction against closing the release-gating backlog item | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conditional-ownership wording added, plus the `ghff0p` `graduated`-not-`done` obligation that preserves the inherited gate |
| PR-206 | LOW | IN-SCOPE | F (honest documentation) | plan F-06 re-measured; `runner_shared.initialize_run_core` | F-06 framed the stale census as "five gates, omitting two". Re-measured: there are at least EIGHT gate calls before the run-directory statement (`refuse_unimplemented_run_flags`, `refuse_unsweepable_run_types`, `refuse_type_scoping_outside_the_review_sweep`, `enforce_dependency_preflight_fn`, `enforce_mixed_type_gate`, `refuse_unrunnable_selected_types`, `enforce_freeze_time_refusal`, `enforce_orchestrator_shape_gate`), so "five" is wrong independently of the two named, and E-05 as authored risked patching a stale five into a stale seven | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 carries the eight-gate re-measurement; E-05 now says DERIVE the census rather than patch it, and must preserve the whole-run-versus-per-artifact distinction that is the comment's actual point, flagging any newly counted gate that refuses per-artifact |
| PR-207 | LOW | IN-SCOPE | G / plan hygiene | plan, between E-05 and `## Project conventions discovered` | Leftover scaffold boilerplate ("Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids") survived into a review-ready plan, inviting an executor to add unreviewed items | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` satisfied vacuously). No `BLOCKER` was found; the one HIGH was fixed in
place.

WHAT I DELIBERATELY DID NOT FLAG. V-01's mutation check (temporarily reverting `lookup_manifest_artifact`
to raise `KeyError`, observing the failure, restoring) is a legitimate sensitivity demonstration and NOT a
code-structure pin: it exercises behavior and asserts on the raised error, exactly what GUIDING_PRINCIPLES
P16 prescribes. V-04's and V-05's content searches over `agent_workflows/` are also not P16 violations,
because they are the reviewer's own verification that retired wording is gone, not shipped test assertions;
the plan is explicit that E-04/E-05 are validated by inspection rather than by a pinning test, and says so
citing P16, which is the correct reading. E-01's value being "it passes today" is honest and correct: F-03
measures that nothing pins the shipped refusal, so a test that passes unchanged is precisely the deliverable.
F-08's four already-correct refusals are a good negative census that keeps E-02 from duplicating them.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02 would have refused runs that succeed today. Fix by scoping, or defer E-02 to the maintainer as a design question? | Scope it, in place, on the existing precedent | Deferring E-02 entirely, rejected because the defect F-02 measures is real and release-gated, and the fix needed was a predicate the codebase already defines rather than a new judgement | `enforce_freeze_time_refusal`'s IPD branch guards on `not is_in_terminal_directory(...)` then `action in ("review", "execute", "orchestrate")`; `action_for` and `success_states_for_action` measured at review | yes |
| D-2 | Should this review answer OQ-01 (does closing `ghff0p` require E-02, or only the retraction)? | No; leave `open` with `Owner: maintainer`, and make the drop path safe | Resolving it YES on the plan's own reasoning, rejected because the question is not answerable from repository evidence: F-02 is confirmed live either way, so what OQ-01 really asks is whether this item or a new one carries it, which is scope-and-bookkeeping the maintainer owns | plan OQ-01's own statement that both readings are defensible; F-02 confirmed live at review; the question is `Blocking: no`, and precedent in this tree shows a non-blocking open question coexisting with `go-pending-approval` | yes |
| D-3 | On the OQ-01 drop path the plan said to mark items "deferred", which is not a legal execution state. Correct the plan, or leave it to the executor? | Correct it, naming `blocked` and its required `Execution note:`, and state the `pre-transition` consequence | Leaving it, rejected because an executor following the literal instruction would write an illegal state and get `IPD-S401`, then improvise at the gate | `ipd_schema.EXEC_STATES`/`VALIDATION_RESULTS` and spec `ipd-structure-and-linting` 5.2/5.3; `IPD-S404`'s every-`E-*`-performed requirement at `pre-transition` | yes |
| D-4 | F-06 said "five gates plus two omitted". Should the review supply the corrected count, or only flag the staleness? | Supply the re-measurement (at least eight) and change E-05 to DERIVE rather than patch | Flagging staleness alone, rejected because the plan would then likely patch five into seven and ship a comment that is still wrong, which is the exact failure mode E-05 exists to end | scan of `initialize_run_core` from its start to `run_dir = state_root(repo) / run_id` at review | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
