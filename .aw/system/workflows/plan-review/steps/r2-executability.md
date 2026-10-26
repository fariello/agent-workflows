# Check R2: Executability

Verify the plan's structural and semantic executability:
- The E/V bijection: each `E-*` item maps 1:1 to a `V-*` item with concrete evidence.
- Scope fence: `- Scope-Paths:` declares all files the plan intends to modify.
- Dependencies: `- Item-Dependencies:` accurately captures all prerequisite plans and their terminal state.
- Concrete evidence in every `V-*`: every validation item demands verifiable, non-tautological evidence.
- No hardcoded counts of mutable record trees.

## Orchestrator checks

#### Orchestrator checklist row check and bounded repair loop (`IPD-S407`)
Beside `review-finalize`, for any plan whose own first `- Kind:` bullet reads `orchestrator`
(read from the plan's own first `- Kind:` bullet in front matter; never use a whole-file containment
scan like `grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as
`m7gvuz`), the linter validates typed child-tracking row conformance (`IPD-S407`).

If `IPD-S407` violations are reported:
1. **Bounded repair loop:** Ask the agent to repair the checklist rows and re-run the check, up to
   an attempt budget of 2 (default 2 per `resolve_retry_budget(None) == 2`; the repository-policy tier
   of that precedence is unimplemented, backlog `dh3us4`).
2. **Verbatim refusal message:** The repair prompt MUST carry child 01's refusal message verbatim
   (which states the invariant, forbids satisfying it by deletion, and names both remedies: moving the
   step to a child with dependencies, or removing it if redundant).
3. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record
   (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording
   the attempt number, what the check reported, what changed, and the row count before and after
   (`rows: N -> M`) so repair by deletion is distinguishable from relocation.
4. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with violations unresolved, the
   plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:`
   is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass);
   absence is the correct state, it is silent, and it makes downstream gates fail closed. (The
   auto-approve predicate reads `- Readiness:` first; `IPD-M107` refuses unattested values).

(Only while the linter does not yet exist may a run record say `machine preflight unavailable:
bootstrap`; once `aw ipd lint` is available that exception no longer applies.)

#### Orchestrator review readiness (`IPD-S408`)
Beside `review-finalize`, for any plan whose own first `- Kind:` bullet reads `orchestrator`, check review readiness with `aw ipd coverage <id6>`.

If coverage findings are reported:
1. **Bounded repair loop:** Resolve each quoted finding by assigning it by id6 to a child in the `## Child IPDs` table or by adding a child plan and its row (never by deleting the checklist), up to an attempt budget of 2.
2. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording the attempt number, what `aw ipd coverage` reported, and what changed.
3. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is the correct state, it is silent, and it makes downstream gates fail closed.

`aw ipd set reviewed` refuses an orchestrator with unresolved coverage findings (Order 05), so the reviewer resolves the findings before setting the status.

### G. Plan executability
Verify the plan states:
- Problem, driver, goals, non-goals, scope, and exclusions.
- Acceptance criteria and ordered implementation steps.
- Target components and existing mechanisms to reuse.
- Dependencies, sequencing, and data/API/workflow effects.
- Security, privacy, migration, documentation, and specification effects.
- Validation, rollout or recovery when relevant.
- Assumptions, open questions, ownership, and follow-up work.
- An execution contract in the gate: resolved open questions, a scope fence, the hard-MUST
  honesty rule (paste the actual runner output), path-scoped commit and never-push, and the
  lifecycle transition (unconditional finalize obligation with conditional runner/executor ownership;
  flag both a hand-rolled `git mv` to `executed/` and an unconditional `aw ipd finalize` instruction).
- For an agent-executable plan: BOTH a top execution checklist AND an end verification/cross-check
  checklist that maps 1:1 with concrete per-item evidence. A weak or absent verification checklist
  (one that could let an agent claim completion without doing every step) is an UNDER-SCOPE finding.
- **Qualified spec citations (post-cutover spec trace convention):** When a plan carries `- From-Spec: <spec-id6>` for a post-cutover spec (filename date `>= 20261001`), every mandatory spec requirement citation in `E-*` items and every acceptance criterion citation in `V-*` items MUST be qualified with `<spec-id6>` (for example `` `89xjll` R-3 `` or `89xjll AC-2`), because `SPEC-PLAN-TRACE` ignores unqualified tokens in both directions (spec 89xjll Section 6.2b).
- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. In contrast, a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts; neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer). A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)
- **Canonical no-error-added proof shape vs. unsatisfiable exit-0 demands (evidence-feasibility convention):** When a plan demands proof that an advisory rule adds no error, the author must demand evidence that can actually be produced. The canonical proof requires two limbs:
  (a) a **registry severity assertion**, showing the rule id resolves through `check_engine.rule_spec` to the intended severity; and
  (b) a **gate-consequence measurement**, driving `artifact_core.drift_exit_code` with the finding list and pasting its return value as a contrastive pair--asserting the real finding list exits 1 (e.g. `drift_exit_code(drift) == 1` for `warning` or `error`) AND that the same finding list with its severity swapped to `info` exits 0 (e.g. `drift_exit_code([d._replace(severity="info") for d in drift]) == 0`). The pair is what localizes the exit code to the severity under test.
  Where the rule is live on the repository corpus, an author may also permit or prefer an optional third limb: a **per-rule count delta** from `python3 -m agent_workflows check all --agent` before and after, showing the new rule id as the only id whose count moved.
  **Anti-pattern to flag:** Demanding "a synthetic tree whose only finding is the new rule, on which `aw check` exits 0" is **unsatisfiable** for any severity other than `info`. In `artifact_core.drift_exit_code`, `info` is the only severity exempted (both `error` and `warning` exit 1; clean/empty trees and `info`-only trees exit 0). `warning` does NOT mean "cannot fail anything"; `error` and `warning` have identical gate consequence (both exit 1) and differ only in condition classification. Writing an exit-0 demand for a non-`info` rule forces the executor to either refuse the item or mis-register the rule as `info`, shipping a contract defect. Reviewers must flag an unsatisfiable exit-0 demand as an in-scope plan defect. Proofs must be behavioral; demanding a source census, caller count, or `read_text`/`inspect` search against `agent_workflows/*.py` is strictly prohibited by GUIDING_PRINCIPLES P16.
- **Runtime-demonstration reachability vs. unsatisfiable observation demands (reachability convention):** For each `V-*` item whose `Required evidence:` demands that the software be **observed** doing something (such as a run, a dispatch, a state transition, or a queue re-evaluation)—as distinct from items demanding a diff, a file's content, a test result, or a search result, which are reachable by construction—the reviewer must verify reachability. The reviewer must **name the code path** (by symbol, per the repository's citation convention) that would produce the demanded observation or **name the sibling `E-*`** that creates that path within the same plan. When neither exists, the reviewer must raise an **UNDER-SCOPE** finding and either add the `E-*` that makes the demonstration reachable or rewrite the demand down to what is observable, recording which remedy was chosen. This check costs one question per runtime-demonstration item and no separate investigation because the reviewer is already reading the cited symbols for rubric G.
  **Measured precedent to flag:** In `akzy45` E-03/V-03, the plan demanded that an item blocked on a prerequisite which later succeeds in the same run become runnable without `--retry-incomplete`. No such code path exists on either host: `requeue_interrupted` and the `if retry_incomplete:` branch both sit outside the dispatch loop in `oc_runipd.run_queue` and `agy_runipd.run_queue`, with zero re-queue calls inside either dispatch loop. That plan was reviewed and approved, and its review round had already re-verified E-03 and corrected its premise once without catching that the surviving demonstration was unreachable. Review is the only enforcement surface; no mechanical lint rule is attempted because verifying reachability requires semantic reading of evidence demands and code paths.

## Review record notes
Record notes in the review record's `### Step R2` subsection starting with `- Checked: <what was examined>`.
