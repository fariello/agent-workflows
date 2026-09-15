# IPD: Parameterize the 8 host-label symbols and lift them to runner_shared

- Date: 2026-09-15
- Kind: child
- Concern: 8 symbols are duplicated across both runners and their ONLY difference is a host-identifying string (`aw oc run` vs `aw agy run`, a report title, an argv token). They cannot be lifted as-is like child 03's 48, and they must not be left forked, because the shared logic around each string keeps drifting independently.
- Scope: Design ONE host-descriptor the shared library takes as a parameter, then lift these 8 definitions into `runner_shared.py` with the host string supplied by the caller rather than baked in. Logic comes from the `oc_runipd` version per the maintainer's 2026-09-14 ruling; only the string becomes a parameter.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_host_descriptor.py
- Item-Dependencies: executed:i3d6ml
- Status: to-review
- Set: rununify
- Order: 4
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: tx6q0h
- From-Backlog: alw22r

## Workflow history
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a fresh per-symbol diff at HEAD; each of the 8 was inspected and its host-bearing lines counted.

## Goal

Remove the last 8 mechanically-duplicated symbols by giving the shared library a single host descriptor
instead of two copies of the same function that differ only in what they call the host. One definition,
one place to fix, and the host string becomes data rather than code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the descriptor

- [ ] E-01 Define ONE host descriptor in `runner_shared.py` carrying every host-varying string these 8 symbols need, measured from their actual diffs rather than guessed: the command prefix (`aw oc run` / `aw agy run`), the argv tokens `_detect_driver_command` matches (`oc`/`opencode` versus `agy`/`antigravity`, and agy additionally accepts `runagy`), the prompt/report title (`OpenCode IPD Driver Turn` / `Antigravity IPD Driver Execution Report`), and the report's verification column header (`Verify` / `Verification`). Do NOT invent fields no symbol reads; every field must be justified by a named call site.
  - Depends on: none
  - Expected outcome: one descriptor type with two instances (one per host), every field traceable to a symbol that consumes it, and no unused field.
  - Execution state: pending

- [ ] E-02 Lift the four PROMPT/REPORT producers through the descriptor: `build_prompt`, `build_verifier_prompt`, `write_report`, `render_continuation_hint`. Take the oc logic. IMPORTANT, measured: `write_report` differs in more than the title, since oc emits a `- Launch:` line (`render_launch_identity`) and a `Verify` column while agy emits neither and uses `Verification`. Adopting oc's version therefore GIVES agy the launch-identity line; that is a deliberate improvement under the ruling, and it changes agy's report shape, so state it rather than let it surprise a reader.
  - Depends on: E-01
  - Expected outcome: four single definitions; agy's execution report now carries the launch-identity line and the `Verify` header; the shape change is recorded.
  - Execution state: pending

- [ ] E-03 Lift the two POLICY/IDENTITY symbols: `driver_actor` and `enforce_requested_action`. `driver_actor` must keep the parenthesis-free `model=<model>` form both hosts already use, because `attention_contract.actor_refusal` REFUSES a parenthesized actor (plan `fn2l1u`) and the history line wraps the actor in parens. `enforce_requested_action`'s difference is only the name of the action-deriving helper it cites in its own message (`action_for` versus `determine_action`); resolve to whichever name survives child 03's lift and make the message read correctly for both hosts.
  - Depends on: E-01
  - Expected outcome: two single definitions; a parenthesized actor is still refused; the safety content of `--action` is unchanged (it still cannot force a transition or execute an unapproved item).
  - Execution state: pending

- [ ] E-04 Lift the two remaining: `_detect_driver_command` and `_compute_scope_reconciliation`. The first becomes a descriptor lookup over the accepted argv tokens with the descriptor's command prefix as the fallback. The second differs ONLY in the two auto-reconciliation reason strings it writes (`auto-reconciled by aw oc run` / `by aw agy run`), which become the descriptor's command prefix; note that those strings land in a plan's PERMANENT finalize record, so they must still name the host that actually ran.
  - Depends on: E-01
  - Expected outcome: two single definitions; a finalize record still names the correct host in its auto-reconciliation reason.
  - Execution state: pending

### Task group 2: proof

- [ ] E-05 Add `tests/test_rununify_host_descriptor.py`: each of the 8 resolves to the SAME OBJECT from both hosts; each host's descriptor produces its OWN strings (so the parameterization is real and not a hardcoded default); an AST scan proves neither runner still defines any of the 8; and a NEGATIVE case proves a missing descriptor field fails loudly rather than emitting an empty host name into a permanent record.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a suite that fails if the 8 are re-forked, if a host's strings collapse to one host's, or if a descriptor field goes silently empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.py` already uses NAME/VALUE INJECTION for exactly this problem rather than importing a
  host: `run_checked(..., env_builder=)`, `save_state(..., write_report=)`, and plan `b7xarm`'s
  `resume_via_launcher(launcher, ...)`, which was chosen specifically so no third launcher call site
  appears. A host descriptor is the same pattern applied to strings instead of callables.
- `integrate_lane_branch` is the precedent to copy: it already takes `host_label="aw oc run"` so the
  merge subject on main reads `integrate(aw oc run): ...`. That is a one-field descriptor in
  everything but name, and it proves the approach works in this codebase.
- `attention_contract.actor_refusal` refuses a parenthesized actor, so `driver_actor`'s output shape is
  constrained by a live gate, not merely by convention.
- `tests/test_run_flag_surface.py` reads spec `25kzda` 2.1 as a FILE in both directions, so a flag
  surface must not be touched here; none of these 8 registers a flag except `_add_output_mode_flags`,
  which is child 03's and is display-only.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | These 8 are the ONLY shared symbols whose entire behavioral difference is a host-identifying string. Every changed code line in each diff carries a host token. That is what makes a descriptor sufficient and a judgement call unnecessary. |
| F-2 | HIGH | `write_report` | The difference is NOT only the title. oc emits a `- Launch:` line via `render_launch_identity` and a `Verify` column; agy emits neither and spells the header `Verification`. So adopting oc GIVES agy the launch-identity line, an improvement, but it changes agy's report shape and must be disclosed. |
| F-3 | MED | `_detect_driver_command` | agy accepts a THIRD argv token (`runagy`) that oc has no analogue for. The descriptor must carry a LIST of accepted tokens per host, not a single token, or agy loses an invocation spelling. |
| F-4 | MED | `_compute_scope_reconciliation` | Its two host strings are written into a plan's PERMANENT finalize record as the auto-reconciliation reason. A descriptor bug here would misattribute which host reconciled a scope, so this is the one symbol where an empty or defaulted host string is a history-corrupting defect rather than a cosmetic one. |
| F-5 | MED | `enforce_requested_action` | Its diff is only the helper NAME quoted in its own explanatory message (`action_for` vs `determine_action`), which means the two hosts call differently-named functions for the same job. Child 03 lifts one of them; this plan must cite whichever name survives, so it is ordered AFTER child 03 by declared dependency. |
| F-6 | LOW | `driver_actor` | Both hosts already agree on the parenthesis-free `model=` shape because a setter-side gate refuses the alternative. So the only real difference is the command prefix, which the descriptor supplies. |

## Proposed changes (ordered, validatable)

1. Define the host descriptor with only the fields these 8 provably consume (E-01).
2. Lift the four prompt/report producers, disclosing agy's report shape change (E-02).
3. Lift `driver_actor` and `enforce_requested_action`, preserving the actor gate and `--action` safety (E-03).
4. Lift `_detect_driver_command` (token LIST per F-3) and `_compute_scope_reconciliation` (F-4) (E-04).
5. Add the descriptor suite including the negative empty-field case (E-05).

## Deferred / out of scope (with reason)

- The 48 no-disagreement symbols: child 03 (`i3d6ml`), this plan's declared dependency.
- `extract_session_id`, `driver_begin`: child 05. Genuine behavior conflicts, not host strings.
- `PlanRecord`, `parse_plan_file`, `build_dynamic_manifest`: child 06.
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11.
- Renaming `action_for`/`determine_action` to one name repo-wide. This plan CITES whichever survives
  child 03; unifying the name itself is that child's or a later cleanup's, not a string change here.

## Scope check

- Over-scope: none. Three source files plus one new test file.
- Under-scope: the descriptor will likely be useful to children 07 through 11 as well, since the big
  functions carry host strings too. This plan builds it for its own 8 and does not pre-fit it to
  theirs, because designing for unmeasured callers is how a parameter grows fields nobody reads.

## Required tests / validation

1. `tests/test_rununify_host_descriptor.py` (new): object identity across hosts for all 8; each host
   produces its OWN strings; AST scan showing no runner re-defines any of them; and the NEGATIVE case
   proving a missing/empty descriptor field raises rather than writing an empty host name.
2. A REPORT-SHAPE regression for F-2: agy's rendered report gains the `- Launch:` line and the `Verify`
   header, asserted explicitly so the change is pinned rather than incidental.
3. `tests/test_agy_runipd_cli.py` and `tests/test_oc_runipd.py` green (both render reports and prompts).
4. `tests/test_run_summary_table.py` and `tests/test_reporting_contract.py` green, since they read
   report/prompt output shape.
5. Bare `python3 -m pytest`, summary pasted, no new failure against the baseline at execution time.
6. NON-VACUITY: force the descriptor to return oc's strings for BOTH hosts and show the suite FAILS
   naming agy, then restore. Without this, a test asserting "each host produces its own strings" can
   pass while both silently resolve to one host.

## Spec / documentation sync

No `.spec.md` change. These are internal producers, and the operator-visible surfaces they emit
(prompt text, execution report) are not spec-pinned in shape. ONE disclosure belongs in the execution
report rather than a spec: agy's report gains a `- Launch:` line and its verification column is renamed
(F-2).

## Open questions

### OQ-01: Does agy gaining oc's `- Launch:` report line count as a behavior change this Set forbids?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: It is a REPORT-CONTENT change, not a runner-behavior change, and it
  is the direct consequence of the maintainer's standing ruling that oc is the preferred version. The
  parent's constraint is that a child may not change what a runner DOES; emitting the launch identity a
  human reads is additive disclosure, and agy's omission of it is closer to a defect than a feature.
  Recorded in E-02 and asserted in Required tests item 2 so it cannot land silently.

### OQ-02: Should the descriptor be a dataclass, a NamedTuple, or a plain mapping?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: Whatever the executor picks, it must FAIL LOUDLY on a missing field,
  which is the property F-4 makes load-bearing (a silently empty host name would be written into a
  permanent finalize record). A plain mapping with `.get()` is therefore the one form to avoid. The
  choice between a frozen dataclass and a `NamedTuple` is left to the executor since both raise on a
  missing attribute; `runner_shared` already uses `NamedTuple` widely, so that is the path of least
  surprise.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the descriptor definition pasted, with each field annotated by the symbol and line that consumes it; plus a statement that no field is unconsumed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted identity results for the four producers; a BEFORE/AFTER of agy's rendered execution report header showing the `- Launch:` line appearing and the column renamed; and the pasted assertion that pins it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted identity results for both symbols; a pasted demonstration that a parenthesized actor is STILL refused; and the `--action` safety assertions still green by name.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted identity results; a demonstration that agy still resolves its `runagy` argv token (F-3); and a pasted finalize auto-reconciliation reason naming the correct host for EACH host (F-4).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THREE parts, all pasted. (a) `python3 -m pytest tests/test_rununify_host_descriptor.py -o addopts=""` green. (b) The NON-VACUITY control: descriptor forced to oc's strings for both hosts produces a named failure, then restored green. (c) Bare `python3 -m pytest` with no new failure, plus the four named existing suites green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS: F-4 (an empty descriptor field here corrupts a permanent finalize
record, so the negative test in E-05 is the one that matters most), F-3 (dropping agy's third argv
token would silently break an invocation spelling), and F-2's disclosed report-shape change.
