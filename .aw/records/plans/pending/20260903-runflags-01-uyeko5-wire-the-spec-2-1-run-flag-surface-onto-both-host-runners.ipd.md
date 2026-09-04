# IPD: wire the spec 2.1 run flag surface onto both host runners

- Date: 2026-09-03
- Kind: child
- Concern: Spec `25kzda` 2.1 declares the invocation surface of `aw <host> run` as a closed flag list. SEVEN of its eight policy flags are unreachable from the command line, and the failure is systematic rather than a gap in one feature: the POLICY LANDS AND THE OPERATOR SURFACE DOES NOT. Measured at HEAD `eb8d008e`: `--full-auto` is the ONLY one registered in either runner's parser. `--allow-mixed` and `--unattended` have working policy logic in `run_selection_policy.py` with NO flag to reach it, and worse, `run_selection_policy.decide` (`:575`) has ZERO callers anywhere in the package - the entire mixed-type gate that executed plan `6lu3rq` built is dead code. `--allow-unverifiable`, `--unverifiable-ok`, `--retry-budget`, `--follow-generated` and `--with-dependencies` do not exist in any form. So a documented CLI contract is, in the operator's hands, one flag wide.
- Scope: Register the seven missing spec-2.1 flags on BOTH host runners' `run` and `resume` parsers, thread each to the policy predicate that already decides it, and freeze the values into run state per the spec's resume rule. Wires up existing predicates and creates NO new policy: where a predicate exists it is CALLED, never reimplemented; where none exists the flag is registered and refuses honestly rather than silently accepting. Excludes writing the mixed-type gate (`6lu3rq` built it; this plan CONNECTS it), excludes the `--unverifiable-ok` aggregation rule (`zub5f1` owns the predicate), excludes the retry-budget range check (`sq61qd` owns it), excludes `--action` and `--json` (already present or out of this Set), and excludes changing any flag's documented semantics.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_run_selection_policy.py
- Item-Dependencies: executed:818uru
- Status: to-review
- Set: runflags
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: uyeko5
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history

- 2026-09-04 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): ADDED E-07/V-07 by maintainer ruling: NORMALIZE `--full-auto` to default `False` on BOTH hosts. This SUPERSEDES F-5 as originally written, which recorded the per-host divergence (oc `False`, agy `True`) as intentional and told the executor to preserve it. The maintainer ruled the divergence IS the defect. It is a safety fix, not cosmetic: `aw agy run <selector>` currently auto-clears a `reviewed` plan with approving `- Readiness:` to `auto-approved` and executes it with NO flag passed, i.e. execution is opt-OUT on one host and opt-IN on the other. MEASURED THREE SITES PER HOST, so a parser-only fix would leave the old behavior live while the help text claimed otherwise: parser default (`agy_runipd.py:4481`), args fallback (`:1989`), run-state fallback (`:3760`); the oc equivalents are already `False` (`:6300`, `:2929`, `:5470`). No test pins the agy default, so nothing external breaks. Also recorded the one real hazard: a run frozen before this change may carry no `full_auto` key, so the fallback change could alter how an in-flight run resumes, and V-07 requires that be stated rather than discovered. Resume's `default=None` mechanism (F-6) is untouched, being a different concern that is already correct. F-5, V-06 and the scope fence updated in place so no instruction still tells the executor to preserve the divergence.

- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the `runcodes` split (`wlxkoz` -> `zub5f1`/`sq61qd`) surfaced that BOTH children had to work around flags that do not exist: `zub5f1` consumes an admission PARAMETER because `--allow-unverifiable` is unbuilt, and `sq61qd` validates a helper parameter because `--retry-budget` is unbuilt. Recording those as plan findings kept the children honest but left the real gap untracked, which is what this plan fixes. MAINTAINER RULINGS 2026-09-04, both recorded here rather than re-litigated: (1) SCOPE is EVERYTHING - all seven missing flags, not just the two the split exposed, because they are one parser edit in two files and doing them piecemeal means repeatedly reopening the highest-contention modules in the repo; (2) SEQUENCING is AFTER `rununify`, hence `- Item-Dependencies: executed:818uru`, so the flags are wired ONCE into the shared runner library instead of twice into two diverging parsers. FOUR THINGS MEASURED AT AUTHORING, not inherited. (a) Only `--full-auto` is registered (oc `:6298` start / `:6373` resume; agy `:4479` / `:4531`); the other seven grep to zero as parser arguments in both runners. (b) `--allow-mixed` and `--unattended` DO have policy behind them (`run_selection_policy.py:580`, `:644`), so those two are pure wiring. (c) THE MIXED-TYPE GATE IS DEAD CODE: `run_selection_policy` is imported by NOTHING outside its own tests, and `decide` has zero callers, so `6lu3rq`'s executed gate cannot fire today. That is a separate defect this plan is the natural owner of, and it is why E-02 exists. (d) The `--full-auto` DEFAULT ALREADY DIFFERS BY HOST (oc `False` at `:6300`, agy `True` at `:4481`), so "wire both runners identically" would be wrong; per-host defaults must be preserved deliberately.

## Goal

Make every flag spec 2.1 documents actually reachable from `aw oc run` and `aw agy run`, wired to the predicate that already decides it, so the documented contract and the shipped command agree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the gap, then close the two flags whose policy already ships

- [ ] E-01 Write the failing-first CONTRACT TEST before touching a parser: assert that every flag spec 2.1 declares for `aw <host> run` is registered on BOTH runners' `run` parser, driven by a DATA table of flag names taken from the spec rather than hand-written per flag. It must FAIL at current HEAD naming the seven missing flags, for both hosts. Drive it from the spec's list so a future flag added to the spec and not the code fails this test; that is the property that stops this gap recurring, and it is worth more than the individual wirings below.
  Assert REGISTRATION ONLY here (the flag parses and lands in the namespace), not behavior: behavior is E-02..E-05, and conflating them would make this test fail for two unrelated reasons.
  - Depends on: none
  - Expected outcome: one table-driven test, failing at HEAD, naming all seven missing flags per host. Paste the failure.
  - Execution state: pending

- [ ] E-02 Wire `--allow-mixed` and `--unattended`, and CONNECT the dead mixed-type gate. These two are pure wiring because the policy already ships: `run_selection_policy.decide` (`:575`) takes `allow_mixed` and `interactive` and returns a typed `Verdict`, with the `RUN-MIXED-TYPES` refusal already composed (`:294`, `:621`).
  THE REAL DEFECT HERE IS THAT NOTHING CALLS IT (measured: `run_selection_policy` is imported by no module outside its own tests, and `decide` has zero callers), so executed plan `6lu3rq`'s gate is DEAD CODE and a mixed selection is silently accepted today. Register both flags and add the ONE call site at queue build, before the queue is frozen, passing `interactive` from the real TTY state and `allow_mixed` from the flag. Do NOT reimplement any part of the gate: the exact-phrase confirmation, the counts preview, and the refusal text are all already written and tested, and a second copy would be the fork this repo keeps paying for.
  `--unattended` must mean the same thing the policy already assumes (no interactive prompt available), and note spec 2.1 says `--full-auto` IMPLIES `--unattended` while implying none of the others; implement that implication explicitly rather than leaving it to chance.
  - Depends on: E-01
  - Expected outcome: both flags parse on both hosts; `decide` is CALLED exactly once at queue build with no logic duplicated; a mixed-type selection is now gated (interactive prompt requires the exact phrase, unattended refuses without `--allow-mixed` and proceeds with it); `--full-auto` implies `--unattended`; `6lu3rq`'s gate is reachable, demonstrated live.
  - Execution state: pending

### Task group 2: register the five flags whose behavior another plan owns or nothing owns yet

- [ ] E-03 Register `--allow-unverifiable` and `--unverifiable-ok` and bind them to the predicate `zub5f1` lands. `zub5f1` deliberately takes the admission as a PARAMETER because these flags did not exist; this item supplies them, which is the other half of that seam. Spec 2.1: `--unverifiable-ok` is legal ONLY when contractless prompts were admitted by `--allow-unverifiable` or the interactive `run unverifiable` confirmation, so passing it alone must be REFUSED at the parser/policy boundary rather than silently honored.
  IF `zub5f1` HAS NOT LANDED when this executes, register the flags and route them to a single clearly-named seam that refuses honestly (documenting that the aggregation predicate is not yet present), and do NOT implement the aggregation rule here. Two implementations of one aggregate rule is worse than one missing flag. State which case applied.
  - Depends on: E-01
  - Expected outcome: both flags parse on both hosts; `--unverifiable-ok` without its precondition is refused with a message naming the missing admission; when `zub5f1` is present the flag reaches ITS predicate and no aggregation logic is duplicated here.
  - Execution state: pending

- [ ] E-04 Register `--retry-budget <0..10>` and bind it to the shipped helpers, respecting the precedence spec 2.1 fixes: CLI value overrides repository policy, repository policy overrides the default of 2. `sq61qd` owns the 0..10 RANGE VALIDATION on `plan_retry`/`retry_budget_remaining`; this item owns the FLAG and the precedence, and must call that validation rather than re-checking the range itself.
  DO NOT CHANGE `DEFAULT_RETRY_LIMIT` (`run_recovery.py:62`, currently `2` by maintainer ruling 2026-08-31). If repository policy has no existing home, do NOT invent a config surface here: implement CLI-over-default and record that the middle tier is unimplemented, rather than adding a policy file this plan has not designed.
  - Depends on: E-01
  - Expected outcome: the flag parses on both hosts and reaches the shipped helpers; an out-of-range value is refused (by `sq61qd`'s validation if present, else by this flag's own bound with the duplication recorded as temporary); the default remains 2; precedence is demonstrated, and any unimplemented tier is stated rather than faked.
  - Execution state: pending

- [ ] E-05 Register `--follow-generated` and `--with-dependencies`. NEITHER has any implementation anywhere (both grep to zero), and that makes this the item most likely to go wrong: `--with-dependencies` means "expand the selection to the transitive declared dependency closure BEFORE the queue is frozen, and subject any newly introduced type to the same mixed-type gate" (spec 2.1), which is real graph work, and `--follow-generated` means newly generated IPDs JOIN the active graph rather than being reported as next actions.
  DO NOT BUILD EITHER BEHAVIOR HERE. Register both flags and make each REFUSE with `not yet implemented` naming what is missing. A flag that parses and silently does nothing is strictly worse than no flag, because the operator believes the dependency closure was expanded when it was not, and that is a correctness failure rather than a UX one. If you judge the closure expansion small enough to build, that is a SEPARATE plan with its own review, and say so rather than widening this one.
  - Depends on: E-01
  - Expected outcome: both flags parse and are visible in `--help`, and both refuse with a clear `not yet implemented` message naming the missing capability; NEITHER silently no-ops; a follow-up is named for the real behavior.
  - Execution state: pending

### Task group 3: freeze the values, and prove both hosts agree

- [ ] E-07 NORMALIZE `--full-auto` TO DEFAULT `False` ON BOTH HOSTS. MAINTAINER RULING 2026-09-04: it should be `False` for both, so this supersedes F-5's "preserve the per-host default" instruction, which recorded the measured divergence as intentional; it was not, and the divergence is the defect.
  WHY THIS IS A SAFETY FIX AND NOT COSMETIC: `agy_runipd.py:4481` declares `default=True`, so `aw agy run <selector>` TODAY auto-clears any plan whose `Status: reviewed` and whose `- Readiness:` is approving to `auto-approved` and executes it, with NO flag passed and no human approval, unless the operator remembers `--no-full-auto`. The opencode host defaults `False` and requires opting IN. Two hosts disagreeing about whether execution is opt-in or opt-out is exactly the class of divergence the `rununify` Set exists to remove, and here it defaults to the LESS safe direction.
  THREE SITES PER HOST, not one, and missing the last two would leave the old behavior in place while the flag help claims otherwise. Measured: the parser default (`agy_runipd.py:4481`), the args fallback (`:1989`, `getattr(args, "full_auto", True)`) and the run-state fallback (`:3760`, `state.get("options", {}).get("full_auto", True)`). The opencode equivalents are already `False` at `oc_runipd.py:6300`, `:2929`, `:5470`; make agy match all three. Leave the `resume` re-declaration at `default=None` on both hosts (F-6): that is a different mechanism and is already correct.
  RESUME COMPATIBILITY, which is the one real hazard here: a run frozen BEFORE this change may carry no `full_auto` key in its options, and changing the fallback silently changes how such a run resumes. Check whether any state on disk relies on the old default, and if a frozen run could flip behavior, record it rather than letting an in-flight run change meaning mid-resume.
  - Depends on: E-01
  - Expected outcome: both hosts default `--full-auto` to `False` at all three sites; `aw agy run` no longer auto-approves without the flag; `--full-auto` still works when passed explicitly on both hosts; the resume `default=None` behavior is unchanged; any pre-existing frozen-state implication is stated.
  - Execution state: pending

- [ ] E-06 Freeze every wired flag into run state and honor the spec's RESUME rule: "`--resume` is mutually exclusive with a new selector and with flags that would change the frozen queue or policy", and specifically "the frozen value cannot change on resume" for `--retry-budget`. Both runners already have a SEPARATE `resume` parser (oc `:6373`, agy `:4531`) where `--full-auto` is re-declared with `default=None` so an absent flag does not clobber the frozen value; FOLLOW THAT EXISTING PATTERN for each new flag rather than inventing one, and note it is why `default=None` matters on resume.
  DEFAULTS: `--full-auto` is NORMALIZED to `False` on both hosts by E-07 (maintainer ruling 2026-09-04), so do not re-diverge it here. For every OTHER flag, the FLAG SET must match across hosts while any existing per-host default stays as documented; do not silently harmonize a default this plan was not told to normalize.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: every wired flag is frozen into run state at queue build; passing a policy-changing flag with `--resume` is refused; an absent flag on resume does not clobber the frozen value; per-host defaults are unchanged, shown side by side.
  - Execution state: pending

## Project conventions discovered (Step 0)

- BOTH RUNNERS HAVE TWO PARSER SITES, `run`/start and `resume`, and a flag must be considered for both. The shipped `--full-auto` shows the intended shape: declared with a real default on start, re-declared `default=None` on resume so an omitted flag cannot overwrite frozen state.
- `run_selection_policy.decide` is PURE by design (no TTY, no filesystem): the caller performs the prompt and hands the typed response in, "which is what makes every branch testable". Any wiring must keep the prompt in the caller.
- `Verdict.WAIVES` and `decide`'s docstring record that `allow_mixed` is deliberately the ONLY override that predicate accepts, "so this predicate can never become the place another gate is waived". Do not add a second override to it.
- The runners are the highest-contention files in the repo. `Item-Dependencies: executed:818uru` exists so this plan edits the post-extraction shape ONCE rather than racing the `rununify` Set.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | SEVEN of spec 2.1's eight policy flags are unreachable. Only `--full-auto` is registered, in either runner. | `--full-auto` at `oc_runipd.py:6298`/`:6373`, `agy_runipd.py:4479`/`:4531`; `--allow-mixed`, `--unattended`, `--allow-unverifiable`, `--unverifiable-ok`, `--retry-budget`, `--follow-generated`, `--with-dependencies` all grep to ZERO as parser arguments in both runners |
| F-2 | **THE MIXED-TYPE GATE IS DEAD CODE, and this is the most serious finding here.** Executed plan `6lu3rq` built the whole gate (exact-phrase confirmation, counts preview, verbatim `RUN-MIXED-TYPES` refusal) in `run_selection_policy.py`, and NOTHING calls it: the module is imported by no other module in the package, and `decide` has zero call sites. So a mixed-type selection is silently accepted today despite an executed plan claiming the gate. | `run_selection_policy.decide:575`; `grep -rn "run_selection_policy" agent_workflows/*.py` returns only two unrelated COMMENT mentions in `selectors.py`; `RUN_MIXED_TYPES:294` used only at `:621` inside the same module |
| F-3 | `--allow-mixed` and `--unattended` are PURE WIRING: the policy exists and takes them as parameters, so E-02 adds no logic. | `run_selection_policy.decide` signature at `:580` (`allow_mixed: bool = False`), used at `:644`; `interactive` in the same signature |
| F-4 | `--allow-unverifiable`, `--unverifiable-ok`, `--retry-budget`, `--follow-generated`, `--with-dependencies` have NO implementation anywhere in the package, not merely no flag. The first three have an owner (`zub5f1`, `sq61qd`); the last two have none. | each greps to zero under `agent_workflows/` except as prose: `run_selection_policy.py:168` mentions unverifiable admission, `run_recovery.py:49` mentions the retry default |
| F-5 | THE `--full-auto` DEFAULT DIFFERS BY HOST: oc `False` (opt in), agy `True` (opt OUT). **SUPERSEDED 2026-09-04 BY MAINTAINER RULING: normalize BOTH to `False` (E-07).** As first recorded, this finding said the defaults must NOT be harmonized; the maintainer ruled the divergence is itself the defect, and it defaults to the less safe direction - `aw agy run` currently auto-approves and executes a reviewed plan with no flag passed. Three sites per host, not one: parser default, args fallback, run-state fallback. | `oc_runipd.py:6300`/`:2929`/`:5470` (all `False`); `agy_runipd.py:4481`/`:1989`/`:3760` (all `True`) |
| F-6 | THE RESUME PATTERN ALREADY EXISTS and must be followed: each runner re-declares `--full-auto` on its `resume` parser with `default=None`, so an absent flag does not clobber the frozen value. | `oc_runipd.py:6373-6375`, `agy_runipd.py:4531-4533` |
| F-7 | PROVENANCE: this plan exists because the `runcodes` split forced two children to work around missing flags rather than fix them. `zub5f1` takes the admission as a parameter; `sq61qd` validates a helper parameter. Both are correct in isolation and both leave the operator with no flag. | `zub5f1` F-3 and OQ-01; `sq61qd` F-3 |
| F-8 | CONTENTION, and the reason for the dependency edge: both runner modules are declared by 11 other unexecuted plans including seven `reviewed` `lanectn` plans, `prpipy`, and both `rununify` children. Sequencing after `818uru` means the flags are wired once into the extracted shape. | computed Scope-Paths intersection across `pending/`; this plan's `- Item-Dependencies: executed:818uru` |

## Proposed changes (ordered, validatable)

1. Table-driven contract test over spec 2.1's flag list, failing at HEAD for both hosts (E-01).
2. Wire `--allow-mixed`/`--unattended` and add the single call site that makes `6lu3rq`'s gate reachable (E-02).
3. Register the two unverifiable flags, bound to `zub5f1`'s predicate or an honest refusal (E-03).
4. Register `--retry-budget` with the spec's precedence, calling `sq61qd`'s validation (E-04).
5. Register `--follow-generated`/`--with-dependencies` as explicit `not yet implemented` refusals (E-05).
6. Freeze the values, honor the resume rule, preserve per-host defaults (E-06).

## Deferred / out of scope (with reason)

- BUILDING `--with-dependencies` CLOSURE EXPANSION and `--follow-generated` GRAPH JOINING. Real graph work with its own correctness surface (the closure must be expanded before freezing AND subject new types to the mixed-type gate). E-05 registers them refusing rather than silently no-opping, and a follow-up plan owns the behavior.
- THE `--unverifiable-ok` AGGREGATION RULE: `zub5f1` owns it. This plan supplies the flag and the precondition refusal only.
- THE RETRY-BUDGET 0..10 RANGE CHECK: `sq61qd` owns it. This plan supplies the flag and the precedence.
- THE MIXED-TYPE GATE ITSELF: executed `6lu3rq` built it. This plan CONNECTS it (F-2) and must not reimplement any part.
- A REPOSITORY-POLICY CONFIG TIER for `--retry-budget`. Spec 2.1 names CLI > repo policy > default, and no repo-policy home exists. E-04 implements CLI-over-default and records the missing tier rather than inventing a config surface.
- `--action` AND `--json`: out of this plan's concern; `--action` in particular carries its own legality rules per spec 2.1.

## Scope check

- Over-scope: none. Every edit registers a spec-declared flag, connects it to an existing predicate, or proves both hosts agree.
- Under-scope, DELIBERATE and stated plainly: after this plan, `--follow-generated` and `--with-dependencies` PARSE BUT REFUSE. That is the honest end state for a flag whose behavior nobody has built, and it is strictly safer than accepting them silently, which would let an operator believe a dependency closure was expanded when it was not.
- Under-scope: `--retry-budget`'s middle precedence tier (repository policy) is unimplemented, recorded rather than faked.

## Required tests / validation

- E-01's contract test, demonstrated FAILING at pre-change HEAD and passing after, for BOTH hosts.
- THE DEAD-GATE FIX IS THE LOAD-BEARING EVIDENCE (F-2): show a mixed-type selection being GATED after E-02, and show `decide` actually being invoked (not merely importable). A test that only checks the flag parses would pass while the gate stayed dead, which is exactly the state this plan found.
- `--unverifiable-ok` without its precondition is refused; with `--allow-unverifiable` it is honored.
- `--retry-budget` out of range refused, 0 and 10 accepted, default still 2, precedence demonstrated.
- `--follow-generated` and `--with-dependencies` refuse rather than no-op, shown.
- Resume: a policy-changing flag with `--resume` is refused; an omitted flag on resume does not clobber frozen state.
- BOTH hosts' flag SETS match, and `--full-auto` defaults `False` on both after E-07's normalization (all three sites per host), shown side by side. No OTHER per-host default changes.
- Both driver suites green: `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`.
- Full suite BARE (`python3 -m pytest`), compared against YOUR OWN pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (`tests/test_run_viewer.py` shows ~15 phantom failures in a detached worktree; backlog `dh0uno`).
- `aw check plans` NO-WORSENING against your own fresh baseline; do NOT claim it passes.

## Spec / documentation sync

- This plan makes the shipped CLI match spec `25kzda` 2.1's declared invocation surface. It does NOT change the spec text.
- Where a flag lands as a refusal (E-05) or with a missing precedence tier (E-04), the divergence from the spec's full semantics MUST be recorded in the flag's own `--help` text, not only in this plan, so an operator reading `--help` is not misled.
- If any user-facing doc enumerates `aw oc run` flags, update it; otherwise state N/A with the paths checked.

## Open questions

### OQ-01: Should `--with-dependencies` and `--follow-generated` be registered-and-refusing, or omitted until built?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING; the plan implements registered-and-refusing and either answer is a small edit to E-05. The case for registering: the spec declares them, `--help` then matches the documented contract, and an operator gets a clear "not yet implemented" instead of `unrecognized arguments`. The case against: a flag that only ever refuses is surface with no capability, and someone may wire it later assuming the behavior exists. The one option NOT on the table is registering them as silent no-ops, which would let an operator believe the dependency closure was expanded when it was not. Chosen default is registered-and-refusing, on the same reasoning `mjx7ne` used for its declared-but-unprobed capabilities (accident prevention beats silence).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the contract test FAILING at pre-change HEAD, with the failure naming all seven missing flags for BOTH hosts, then passing after. Paste the test's DATA table showing it is driven by spec 2.1's flag list rather than hand-written assertions, since that is what makes a future spec flag fail the test instead of being silently missed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `run_selection_policy.decide`'s call site(s) AFTER the change and a grep proving it is called from the runner (it had ZERO callers before; paste the before-grep too, since the dead-gate fix is this item's real deliverable). Then DEMONSTRATE the gate live, not by import: a mixed-type selection under `--unattended` REFUSED without `--allow-mixed` and PROCEEDING with it, and an interactive mixed selection requiring the exact phrase. Paste evidence NO part of the gate was reimplemented (the refusal text still comes from `run_selection_policy`). Paste `--full-auto` implying `--unattended`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both flags in `--help` for BOTH hosts. Paste `--unverifiable-ok` alone being REFUSED with a message naming the missing admission, and honored with `--allow-unverifiable`. State plainly whether `zub5f1` had landed: if yes, paste evidence the flag reaches ITS predicate and no aggregation logic exists in the runner; if no, paste the honest refusal and confirm no aggregation rule was written here.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the flag in `--help` for both hosts, an out-of-range value refused, `0` and `10` accepted, and `DEFAULT_RETRY_LIMIT` still `2`. Paste the precedence demonstration (CLI value beating the default). State which tier is unimplemented and confirm it is recorded in `--help` rather than silently absent. If `sq61qd` had landed, paste evidence its validation is CALLED rather than a second range check added.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste both flags in `--help` for both hosts AND paste each one REFUSING with its `not yet implemented` message. A pasted `--help` alone does NOT satisfy this item: the whole point is that neither flag silently no-ops, and only an observed refusal proves it. Paste the `--help` text showing the not-implemented status is visible to an operator.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste all THREE agy sites showing `False` (parser default, args fallback, run-state fallback) beside the three opencode equivalents, so the normalization is shown complete rather than parser-only. Paste `aw agy run --help` showing the new default. Then DEMONSTRATE the behavior change: a `Status: reviewed` plan with approving `- Readiness:` is NOT auto-approved by a bare `aw agy run`, and IS auto-approved with an explicit `--full-auto`. A pasted default alone does not satisfy this item, since the two fallbacks would keep the old behavior alive while the help text claimed otherwise. State what you found about frozen runs lacking a `full_auto` key.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the frozen flag values read back from run state. Paste a policy-changing flag passed with `--resume` being REFUSED. Paste a resume with the flag OMITTED showing the frozen value survived (this is what `default=None` buys, F-6). Paste both hosts' `--help` side by side showing the flag SETS match AND that `--full-auto` now defaults `False` on BOTH (E-07's normalization; the earlier requirement to preserve `True` on agy was superseded by maintainer ruling 2026-09-04). Any OTHER per-host default must be unchanged. Then both driver suites and the bare full suite with counts, compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 7 E-leaves across 3 task groups, one concern throughout: make spec 2.1's declared flag surface reachable. Right-sizing assessed per item rather than by count: each E-item is one coherent pass with its own test surface (E-01 the contract test, E-02 the two wired flags plus the dead-gate call site, E-03/E-04/E-05 one flag pair each grouped by who owns the behavior, E-06 the freeze and cross-host parity). E-02 is the densest because connecting the gate is inseparable from wiring the flag that reaches it: a flag with no call site would be the same dead surface this plan exists to remove.

Open questions: OQ-01 (register-and-refuse versus omit) is non-blocking with a recorded default. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It also has a hard prerequisite: `- Item-Dependencies: executed:818uru`, by maintainer ruling 2026-09-04, so the flags are wired once into the extracted shared runner shape rather than twice into two diverging parsers.

Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, and `tests/test_run_selection_policy.py`. Do NOT modify `run_selection_policy.py`'s LOGIC: this plan calls `decide`, and adding a second override to it is explicitly forbidden by its own docstring. Do NOT implement the `--unverifiable-ok` aggregation rule (`zub5f1`) or the retry range check (`sq61qd`). Do NOT build the dependency closure or generated-IPD following (E-05 registers refusals only). Do NOT change `DEFAULT_RETRY_LIMIT`. DO normalize `--full-auto` to `False` on both hosts (E-07, maintainer ruling 2026-09-04), at all THREE sites per host; do NOT harmonize any OTHER per-host default as a side effect, and do NOT touch the resume `default=None` mechanism. Do NOT add a repository-policy config surface. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt).

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is (1) E-01's contract test observed FAILING, and (2) the mixed-type gate observed GATING a real selection, because the gate was importable and fully tested while being completely unreachable - a green suite proved nothing about it. Do NOT report `--follow-generated` or `--with-dependencies` as implemented: they parse and refuse. Do NOT claim `aw check plans` passes; the bar is no-worsening against your own fresh baseline.

Execution contract: RE-READ both runner modules immediately before editing and locate every parser site BY SYMBOL, never by the line numbers in this plan: these are the highest-contention files in the repo, `818uru` will have just restructured them by the time this runs, and 11 other unexecuted plans declare them. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
