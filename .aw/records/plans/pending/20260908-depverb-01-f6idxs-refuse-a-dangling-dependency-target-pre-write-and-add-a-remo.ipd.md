# IPD: Refuse a dangling dependency target pre-write and add a remove verb

- Date: 2026-09-08
- Kind: child
- Concern: `aw ipd dependencies set` validates the dependency GRAMMAR before writing but not the target's EXISTENCE, so a typo is accepted and written, and the error arrives later from a different surface (`aw check`). That directly contradicts the maintainer's stated requirement that "the id6/setid MUST be validated before it can be set or removed". Separately there is no `remove` subcommand at all, so dropping ONE edge from a many-edge statement means re-stating the whole list by hand, which is the hand-editing the verbs exist to prevent and which silently races a concurrent edit.
- Scope: The two gaps that are unambiguous and self-contained. IN: pre-write existence validation with an explicit escape hatch for a deliberate forward reference, and a `remove` subcommand that drops a single edge idempotently. OUT: source-side dependency fields on backlog and specs, setid-valued edges, and a close-time dependency gate, each of which needs a design decision or a prerequisite this plan does not own.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_dependency_verb.py
- Item-Dependencies: none
- Status: to-review
- Set: depverb
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: f6idxs
- From-Backlog: rxoazt

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rxoazt`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite `Priority: high`. THIS IS A NARROWING: the item names FIVE gaps and this plan graduates TWO, with the reasons per gap recorded below and in Deferred. ALL FIVE RE-VERIFIED AT HEAD `a2e0438a` and all five are still live, so nothing is graduated as obsolete; the narrowing is about ownership and prerequisites, not staleness. GAP 4 (validation not pre-write) reproduces exactly: `aw ipd dependencies set <plan> exists:backlog:zzzzzz --dry-run --yes` reports `unchanged (dry-run)` and exits 0, although `zzzzzz` matches no artifact. GAP 2 (no remove) reproduces: `aw ipd dependencies --help` shows the subcommand choices as `{set}` only. GAP 1 reproduces: `aw backlog new`, `aw backlog set` and `aw specs set` each return zero matches for a dependency flag. GAP 3 reproduces and is CORRECT-BY-DESIGN today: `exists:backlog:worksequence` is refused pre-write with "exists target 'worksequence' is not a 6-char base36 id6. Refusing before making changes." and exit 2, which is the grammar path working. THE ITEM'S OPEN QUESTION IS NOW ANSWERED BY EVENTS, which is the main change since filing. It asks whether this item should be MERGED INTO `2k42zu` (`worksequence`), which owned the generalize-dependencies-beyond-plans question, and says to decide that before authoring. `2k42zu` IS NOW `done`, closed 2026-09-05 by the execution of IPD `i6015i` (the `aw next --order-by` work) with that plan cited as its evidence. So there is no live sibling to merge into, and this item correctly stays separate as the narrower CLI/validation item. That also REMOVES the stated blocker on GAP 1, but GAP 1 is still deferred here for a different reason recorded in Deferred: it is a spec-sanctioned follow-on that adds a FIELD to two artifact types, which is a data-model change deserving its own plan rather than riding along with a setter fix. GAP 3's prerequisite is unchanged and still open: `sjsoqq` (`setiduniq`, cross-type setid uniqueness) is `open`, and the item calls it "a likely prerequisite" because a setid edge could resolve ambiguously until it lands.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the dependency setter honor its own contract. A target that does not exist should be refused before anything is written, in the same breath as a malformed one, and removing one edge should be a verb rather than a hand-rewrite of the whole statement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: validate existence before writing

- [ ] E-01 Resolve every dependency TARGET and refuse pre-write when it matches no artifact, in `run_dependencies_set_command` (`agent_workflows/status_set.py:1515`). The function already validates and canonicalizes the grammar BEFORE any write via `ipd_schema.canonical_item_dependencies` and refuses with "Refusing before making changes." (`:1558`), so this adds an EXISTENCE check alongside the existing GRAMMAR check at the same point, reusing that refusal contract and its wording rather than inventing a second failure shape. Resolve the target through the shared selector resolver so the setter agrees with `aw find` and with `aw check`; do NOT hand-roll a filesystem scan. Cover all three edge forms the grammar admits, since each names a target differently: `executed:<id6>`, `exists:<type>:<id6>` and `state:<type>:<status>:<id6>`. MEASURED at HEAD `a2e0438a`: `exists:backlog:zzzzzz` is accepted today with exit 0 on a dry run.
  - Depends on: none
  - Expected outcome: a dangling target in any of the three forms exits nonzero with nothing written; a valid target still succeeds; the refusal text matches the existing pre-write refusal contract.
  - Execution state: pending

- [ ] E-02 Add the explicit escape hatch the item requires a decision on, rather than leaving today's accidental permissiveness. The item is direct: "authoring a chain top-down may legitimately need a forward reference to a plan that does not exist yet, so either require `--allow-dangling` for that case or require the target to exist unconditionally, but decide it rather than leaving today's accidental permissiveness." IMPLEMENT `--allow-dangling`, because the forward-reference case is real in this repository (Sets are routinely authored parent-first with children named before they exist) and an unconditional requirement would make that workflow impossible. The flag must be LOUD, not silent: print which targets were accepted as dangling, so the deferral is visible in the transcript, and note the edge remains fail-closed at the repository gate afterwards because `aw check` still reports it (`check.ipd-dependency-dangling` is `error` severity).
  - Depends on: E-01
  - Expected outcome: without the flag a dangling target refuses; with it the write proceeds and NAMES each dangling target; `aw check` still reports the dangling edge afterwards.
  - Execution state: pending

### Task group 2: add the remove verb

- [ ] E-03 Add `aw ipd dependencies remove <selector> <edge...>`, registered beside `set` in `cli.py`. MEASURED: the subcommand choices are `{set}` only, so `aw ipd dependencies remove ...` is an argparse invalid-choice error today. Implement it by REUSING the same machinery `set` uses rather than writing a second write path: `run_dependencies_set_command` drives a same-status no-op transition through `run_set_command` carrying the canonicalized value in `args.item_dependencies`, so persistence-on-no-op is inherited. Removal is therefore "parse the current statement, drop the named edges, canonicalize, write the remainder", and when the remainder is empty it must write the explicit zero `none` rather than an empty string, since `none` is the grammar's zero and an empty value would be malformed.
  - Depends on: none
  - Expected outcome: removing one edge from a multi-edge statement leaves the others byte-identical; removing the last edge yields `none`; the write goes through the existing no-op transition path.
  - Execution state: pending

- [ ] E-04 Define the ABSENT-EDGE semantics deliberately, per the item: "remove a single edge idempotently, and error (not silently no-op) when the named edge is absent, unless a `--if-present` style flag is passed." So the default is an ERROR naming the edge that was not found, and `--if-present` downgrades it to a no-op with a notice. The distinction matters because a silent no-op on a typo'd edge would leave the operator believing they removed something they did not, which is the same class of failure as GAP 4 one level up. Also state and test the IDEMPOTENCY property that the item asks for: removing an edge that is already gone under `--if-present` must be a clean no-op, not a partial write.
  - Depends on: E-03
  - Expected outcome: removing an absent edge exits nonzero and names it; `--if-present` makes it exit 0 with a notice and no file change; repeated removal under `--if-present` is stable.
  - Execution state: pending

### Task group 3: prove it and keep one authority

- [ ] E-05 Do NOT add a second evaluator or a second parser, and prove it. Spec `25kzda` section 2.10 is explicit: "All surfaces call this evaluator; none reimplements it." `check_engine.evaluate_ipd_dependencies` (`check_engine.py:2365`) is already consumed by `aw check` (`:2609`), `aw ipd lint` (`ipd_lint.py:1119`), the runner preflight (`oc_runipd.py:2651`) and the opt-in staged-overlay hook (`hooks/ipd_dependency_statement_gate.py:96`). The grammar authority is likewise single: `ipd_schema.parse_item_dependencies` (`:722`) and `canonical_item_dependencies` (`:778`). E-01's existence check must use the shared selector resolver and E-03's removal must use the shared parser; neither may grow a private copy. Verify by grep that no new dependency regex or parallel evaluator was introduced, mirroring the anti-divergence discipline `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` already enforces for the runners.
  - Depends on: E-01, E-03
  - Expected outcome: a grep proving one grammar parser and one evaluator remain; no new regex; the four existing consumers unchanged.
  - Execution state: pending

- [ ] E-06 Test the matrix, and pin the behaviors that must NOT change. Cover: each of the three edge forms with a dangling target refused pre-write; a valid target accepted; `--allow-dangling` accepting and naming; removing one edge of three; removing the last edge yielding `none`; removing an absent edge erroring; `--if-present` downgrading that to a no-op; and the two behaviors that already work correctly and must be preserved, namely the GRAMMAR refusal for a setid-shaped target (`exists:backlog:worksequence` -> exit 2, "not a 6-char base36 id6", nothing written) and the existing clear-by-empty-or-`none` behavior of `set`. Assert the E-01 case FAILS against HEAD `a2e0438a`, where it exits 0. Use a FIXTURE repository, not the live tree, since these are MUTATING verbs.
  - Depends on: E-02, E-04, E-05
  - Expected outcome: nine cases passing in a fixture repo; the dangling-refusal case fails before the change; the setid grammar refusal and the clear path are unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- MOST OF THE REQUESTED MODEL ALREADY SHIPPED, via the `ipddeps` Set (`r7xku3`, `g69y23`, `ovbnyq`, `mp88bl`, all executed), graduated from spec `25kzda` sections 2.7-2.11. The typed field, zero/one/many, a setter, and runner/checker/hook consumption all exist. This plan closes gaps, it does not build the model.
- ONE evaluator is a spec requirement, not a preference: section 2.10 says every surface calls it and none reimplements it. Four surfaces already do.
- The grammar has a single authority in `ipd_schema` and an explicit ZERO value (`none`), which is why an emptied statement must become `none` rather than blank.
- `run_dependencies_set_command` deliberately reuses the hoisted same-status write from `aw ipd set --from-backlog`, so persistence-on-a-no-op is inherited rather than reimplemented. A remove verb should inherit the same way.
- The pre-write refusal contract already exists and has established wording ("Refusing before making changes."), used by both the scope check and the grammar check in `status_set.py`.
- `Item-Dependencies` must not be confused with three neighbours: the intra-plan `Depends on:` E-row field (a different namespace by spec 2.8, where an E-id is never legal in `Item-Dependencies` and an id6 never legal in an E row), `Gate-Kind`/`Gate-Ref` (the item's own blocked state), and `Blocks-Release` (which points at a release).
- The dangling-edge rule is `error` severity at the repository gate, so nothing ships broken today; the defect is that the error arrives LATE and from a different surface.
- Honest limit worth restating: a git pre-commit hook is local, not cloned, and skippable, so the portable authority stays `aw check` plus CI.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | GAP 4 REPRODUCES: `aw ipd dependencies set <plan> exists:backlog:zzzzzz --dry-run --yes` reports `unchanged (dry-run)` and exits 0 although `zzzzzz` matches no artifact. | measured at `a2e0438a` |
| F-2 | GAP 2 REPRODUCES: the subcommand choices are `{set}` only, so there is no `remove`. | `aw ipd dependencies --help` at `a2e0438a` |
| F-3 | GAP 1 REPRODUCES: `aw backlog new`, `aw backlog set` and `aw specs set` all return zero matches for a dependency flag. | measured at `a2e0438a` |
| F-4 | GAP 3 REPRODUCES and today's refusal is CORRECT: a setid-shaped target is refused pre-write with "not a 6-char base36 id6. Refusing before making changes." and exit 2. That is the grammar path working, so GAP 3 is a feature request rather than a defect. | measured at `a2e0438a` |
| F-5 | THE ITEM'S OPEN QUESTION IS ANSWERED BY EVENTS: `2k42zu`, the sibling it asks whether to merge into, is now `done`, closed 2026-09-05 by the execution of IPD `i6015i`. So this item correctly stays separate and there is no duplicate to reconcile. | `.aw/records/backlog/done/...2k42zu...backlog.md`, `- Status: done` and its history record |
| F-6 | GAP 3's prerequisite is still open: `sjsoqq` (`setiduniq`) is `open`, and the item names it a likely prerequisite because a setid edge could resolve ambiguously until it lands. | `.aw/records/backlog/open/...sjsoqq...` at `a2e0438a` |
| F-7 | The pre-write refusal seam already exists and is where E-01 belongs: the grammar check refuses at `status_set.py:1558` with the established wording. | `status_set.py:1515` (function), `:1558` (refusal) |
| F-8 | ONE evaluator is already the reality across four surfaces, so E-05 preserves rather than establishes it. | `check_engine.py:2365` consumed at `:2609`, `ipd_lint.py:1119`, `oc_runipd.py:2651`, `hooks/ipd_dependency_statement_gate.py:96` |
| F-9 | The removal path can inherit the existing write: `set` drives a same-status no-op transition carrying the canonicalized value, so persistence-on-no-op is already solved. | `run_dependencies_set_command` docstring at `status_set.py:1520-1530` |
| F-10 | Nothing else covers this item: no pending or approved plan touches the dependency setter or adds a remove verb. | grep over `.aw/records/plans/pending/` at `a2e0438a` |

## Proposed changes (ordered, validatable)

1. Resolve and refuse a dangling target pre-write for all three edge forms (E-01).
2. Add a loud `--allow-dangling` escape hatch for deliberate forward references (E-02).
3. Add `aw ipd dependencies remove`, reusing the existing write path and writing `none` when emptied (E-03).
4. Make an absent edge an error by default, with `--if-present` downgrading it (E-04).
5. Prove one grammar parser and one evaluator remain (E-05).
6. Pin nine cases in a fixture repo, including the two behaviors that must not change (E-06).

## Deferred / out of scope (with reason)

- GAP 1, SOURCE-SIDE DEPENDENCY FIELDS ON BACKLOG AND SPECS. Spec `25kzda` section 2.92 deliberately deferred this ("A later design may add source-side dependency fields to those types, but the runner must not infer them from prose in v1"), so closing it is a sanctioned follow-on rather than a contradiction. It is nevertheless a DATA-MODEL change adding a field to two artifact types, with its own validation, rendering, check rules and migration questions, and it would dwarf the setter fixes it was bundled with. NOTE the item's stated blocker is GONE (`2k42zu` is `done`, F-5), so this is now unblocked and worth its own plan; it is deferred on size, not on dependency.
- GAP 3, SETID-VALUED EDGES. Two reasons. FIRST, the item itself frames it as an undecided DESIGN QUESTION, not a defect: a setid edge is one-to-many and its membership CHANGES when a plan joins the Set, so "all current members" versus "all members at evaluation time" must be specified deliberately. SECOND, its prerequisite is still open: cross-type setid uniqueness is not hard-enforced (`sjsoqq`, F-6), so a setid edge could resolve ambiguously. Today's refusal is correct behavior (F-4), so nothing is broken while this waits.
- GAP 5, A CLOSE-TIME DEPENDENCY GATE. The item states the decision is open ("refused, warned, or allowed") and flags a hard constraint from `2k42zu`: a close-time gate must not be able to disagree with `aw attention`. That is a policy design question about surface consistency, not a setter fix, and answering it inside this plan would smuggle a behavior change into a validation change.
- CHANGING THE `Blocks-Release` CLOSE GATE. Separate concern with its own predicate (`check_engine.evaluate_blocking_close`), explicitly distinguished from dependencies in AGENTS.md.

## Scope check

- Over-scope: none. Two source modules and one new test module, all required by E-01 through E-04.
- Under-scope: three of the item's five gaps are deferred with reasons (see Deferred). This plan therefore closes the two gaps that need no new design decision and no external prerequisite.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_dependency_verb.py tests/test_runner_item_dependencies.py` for the focused surface, the latter because it holds the anti-divergence guard E-05 respects.
- All nine E-06 cases run against a FIXTURE repository, with exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `python3 -m agent_workflows check` must not gain a diagnostic, and the `check.ipd-dependency-*` rule family must behave exactly as before on unchanged artifacts.

## Spec / documentation sync

Spec `25kzda` sections 2.7-2.11 define the dependency model this plan extends at the CLI layer. E-01 IMPLEMENTS the maintainer's stated "MUST be validated before it can be set" requirement, which the spec's model permits but does not currently mandate at the setter, and E-03 adds a verb the spec does not enumerate. NEITHER changes the FIELD, the GRAMMAR, or the evaluator, so no `.spec.md` is declared in `Scope-Paths`. TWO obligations for the executor. FIRST, read section 2.10's single-evaluator rule and confirm E-05 satisfies it, reporting any place the new code would become a second authority. SECOND, if the spec enumerates the dependency SUBCOMMANDS such that adding `remove` contradicts it, that IS a spec amendment: declare the spec path in `Scope-Paths` and justify it BEFORE editing, per the plan-may-amend-a-spec rule. The `aw ipd dependencies --help` text is generated from the parser and updates by construction.

## Open questions

### OQ-01: Should `--allow-dangling` be the flag name, and should it require a reason?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: DEFERRED on the name, which is cosmetic, but recorded because the REASON question is not. The repository has a precedent for demanding a justification with a deliberate override (`--scope-reason` on the finalize scope gate), and a dangling edge is a similar "I know this looks wrong" assertion. RECOMMENDATION: implement `--allow-dangling` WITHOUT a mandatory reason, because the forward-reference case is routine rather than exceptional here (Sets are authored parent-first) and requiring prose on a routine action trains agents to write filler; the visibility requirement in E-02 (name each dangling target in the output) plus the surviving `aw check` error give the audit trail. A reviewer who considers dangling edges exceptional should ask for the reason instead.

### OQ-02: When `remove` empties a statement, should it write `none` or `unresolved`?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE FROM THE GRAMMAR, recorded so it is deliberate. The grammar admits both `none` and `unresolved`, and they mean different things: `none` asserts there ARE no dependencies, while `unresolved` asserts they have not been determined. Removing the last edge is an assertion that the dependency is GONE, not that it is unknown, so `none` is correct and E-03 specifies it. Confirm against `ipd_schema.canonical_item_dependencies` that `none` is the canonical zero and that an empty string is not accepted, so the emptied statement cannot be written malformed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: for EACH of the three edge forms (`executed:<id6>`, `exists:<type>:<id6>`, `state:<type>:<status>:<id6>`) paste the dangling-target invocation, its UNPIPED exit code, the refusal text, and proof nothing was written (`git diff` empty, or the plan file's `Item-Dependencies` line unchanged). Then paste a VALID target for one form succeeding. Three refusals and one success minimum.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same dangling invocation WITH `--allow-dangling` showing it proceeds, showing the output NAMES the dangling target, and showing the resulting `Item-Dependencies` line. Then paste `aw check` on that artifact afterwards, proving the dangling edge is still reported as an error at the repository gate.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a plan with three edges, the `remove` invocation dropping one, and the resulting line showing the other two BYTE-IDENTICAL. Then paste removing the last edge and the resulting `- Item-Dependencies: none`. Paste a grep or trace proving the write went through the existing no-op transition path rather than a new writer.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste removing an ABSENT edge showing a nonzero UNPIPED exit code and the message naming that edge; then the same with `--if-present` showing exit 0, a notice, and an unchanged file; then a second `--if-present` removal of the same absent edge showing identical output (idempotency).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a grep showing no new `re.compile` mentioning a dependency field name and no second evaluator function; paste the four existing consumer call sites unchanged; paste the `tests/test_runner_item_dependencies.py` result.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all nine cases with commands, UNPIPED exit codes and outcomes, including the two preservation cases (the setid grammar refusal with its exact message, and the existing clear path). Paste the E-01 case FAILING against pre-change code (where it exits 0). Paste the fixture setup proving the tests do not mutate the live tree.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note this graduates TWO of the item's five gaps, with the other three deferred for stated reasons (F-4, F-5, F-6 and Deferred): GAP 1 is now unblocked but too large to ride along, GAP 3 is an undecided design question with an open prerequisite, and GAP 5 is a policy decision about surface consistency.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE these are MUTATING verbs that write plan front matter, so test against a fixture repository and never against the live tree, and re-locate `run_dependencies_set_command` BY SYMBOL at execution time since `status_set.py` is shared by every status verb. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
