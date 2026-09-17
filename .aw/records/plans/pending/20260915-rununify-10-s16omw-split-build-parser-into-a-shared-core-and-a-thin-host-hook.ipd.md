# IPD: Split build_parser into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `build_parser` is written twice (347 lines in `oc_runipd.py`, 264 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 47 differing code lines of which only 23 bear a host token, so most of the divergence is DRIFT in shared logic rather than genuine host specificity, and every fix to one copy is a fix the other silently misses. CORRECTED AT REVIEW 2026-09-16, AND THE CONCLUSION INVERTS. The 47 and 23 reproduce (22 by my regex), but 47 differing lines out of 46/47 total normalized lines means the two functions share ALMOST NOTHING: SequenceMatcher similarity is 0.4946, by far the LOWEST of the five large functions (against 0.851 for `execute_item` and 0.9345 for `initialize_run`). And the residue is not drift: measured flag-by-flag, the two parsers register 17 SHARED flag strings, 7 OC-ONLY and 10 AGY-ONLY, and `--no-verify` maps to a DIFFERENT dest on each host (`validate` on oc, `no_verify` on agy) by deliberate design that agy enforces with a build-time collision guard oc does not have. So "most of the divergence is DRIFT" is the opposite of what the code shows. See F-6 through F-12 and OQ-03.
- Scope: Extract the host-neutral core of `build_parser` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: the split is GATED on OQ-03, because the measured shared content is 17 flag strings that are ALREADY registered from shared code (`runner_shared.register_run_policy_flags`, 12 spec-governed rows) plus four subparser skeletons, while everything else is each host's own CLI contract. The oc-preferred ruling cannot apply to a flag surface: adopting oc's `--verify`/`--audit` aliases on agy would COLLIDE with agy's shipped `--no-verify`, which is exactly what `assert_verification_flags_are_distinct` exists to catch.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_build_parser.py, tests/test_run_flag_surface.py
- Item-Dependencies: executed:tx6q0h
- Status: approved
- Readiness: go-pending-approval
- Set: rununify
- Order: 10
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: s16omw
- Approval: 2026-09-17, human ("approved"): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 12 findings (PR-001..PR-012), 10 FIXED, PR-001/PR-002 OPEN and escalated as blocking OQ-03. The counts reproduce and the CONCLUSION inverts: 47 differing lines out of 46/47 total means similarity 0.4946, the LOWEST in the Set, and the flag surface is 17 shared / 7 oc-only / 10 agy-only with `--no-verify` deliberately mapping to different dests per host.

- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-001 through PR-012 (10 FIXED, PR-001 and PR-002 OPEN and escalated as the new blocking OQ-03). THE NUMBERS REPRODUCE AND THE INFERENCE INVERTS, which makes this the mirror image of sibling `orziju`. Verified at HEAD `7936c13d`: 347/264 raw lines, 271/212 code lines, 47 differing lines under AST normalization with docstrings stripped, 22 bearing a host token (the plan says 23; close enough to be a rounding of the same measurement). BUT 47 differing lines out of 46 oc and 47 agy TOTAL normalized lines means the functions share almost nothing, and SequenceMatcher agrees: similarity 0.4946, the LOWEST of the five large functions by a wide margin (`initialize_run` 0.9345, `execute_item` 0.851). So the Concern's "most of the divergence is DRIFT in shared logic" is FALSE HERE; F-1's own instinct ("the MOST host-specific of the five") is the correct reading and the Concern contradicts it. MEASURED THE FLAG SURFACE FLAG-BY-FLAG, which no prior review of this Set did: 17 shared option strings, 7 OC-ONLY (`--agent`, `--audit`, `--auto`, `--opencode`, `--variant`, `--verify`, `--verify-with`), 10 AGY-ONLY (`--agy`, `--agy-executable`, `--dangerous`, `--dangerously-skip-permissions`, `--effort`, `--new-session`, `--no-audit`, `--no-dangerously-skip-permissions`, `--no-verify`, `--timeout`). THE SHARPEST FINDING: `--no-verify` resolves to dest `validate` on oc and dest `no_verify` on agy, and `--verify`/`--audit` exist ONLY on oc. That is not drift, it is an intentional incompatibility that agy DEFENDS with a build-time guard `assert_verification_flags_are_distinct` (`agy_runipd.py:1959`), whose docstring records the measured hazard: registering oc's alias list on agy would make `BooleanOptionalAction` auto-generate `--no-verify`/`--no-audit` and, under `conflict_handler="resolve"`, SILENTLY STEAL agy's shipped spellings. oc has no such guard and needs none. So the Set's oc-preferred ruling CANNOT be applied here, and F-2's warning not to touch a flag is not merely a caution but a proof that the oc version cannot win. WHAT IS ACTUALLY SHARED, measured: the 12 spec-governed `RUN_POLICY_FLAGS` rows already registered through `runner_shared.register_run_policy_flags` (both hosts call it twice, F-3 is CORRECT), the four subparser skeletons, and `--repo`/`run_id`/`--json` on `status`/`report` which are byte-identical. THE GOOD NEWS THE PLAN DOES NOT CLAIM, and it is the reason this is the most executable of the five: the closure is the CLEANEST in the Set (7 free names, only TWO still double-defined: `_add_output_mode_flags` and `_detect_driver_command`; `ACTION_CHOICES` and `DEFAULT_STALL_TIMEOUT` are equal constants), and there are ZERO source-inspection pins on `build_parser` (against 14 for `execute_item` and 11 for `initialize_run`), because 31 test files call `build_parser()` BEHAVIORALLY. A relocation here breaks no pin. ALSO CORRECTED: `Item-Dependencies: executed:tx6q0h` gains only ONE of the two remaining symbols, since child 04 lifts `_detect_driver_command` and explicitly ASSIGNS `_add_output_mode_flags` to child 03, which was re-scoped to 9 symbols and does not lift it, so neither sibling clears it; and 50 percent of oc's `build_parser` source is string-literal content (41 percent on agy), so F-5's "help/usage text: supplied by child 04's descriptor" understates the volume by an order of magnitude. REVISED IN PLACE: flag-surface table added to the Goal, the verification-dest collision added as F-7, the zero-pin and clean-closure findings recorded as F-9/F-10 (the two GOOD findings in this plan), the Concern corrected, gating E-01 added, the split narrowed to E-04's analysis, five items in place of three, `tests/test_run_flag_surface.py` fenced, non-vacuity made bidirectional. NOT DECIDED: whether a parser whose shared content is already shared is worth a shared core at all.

- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a per-symbol diff measured at HEAD; the differing lines were counted and classified rather than estimated.

## Goal

Give `build_parser` ONE implementation of everything that is not host-specific, so a fix lands once and reaches
both hosts, without changing what either runner does.

RESTATED AT REVIEW 2026-09-16, because the measurement shows the goal is ALREADY LARGELY MET and what
remains is deliberately host-specific. Measured flag-by-flag across all four subparsers:

| Flag class | Count | Notes |
|---|---|---|
| SHARED option strings | 17 | includes `--repo`, `run_id`, `--json`, `--session`, `--stall-timeout`, `--model`, `--action`, `--manifest`, `--runbook`, `--max-items-per-session`, `--prepare-only`, `--validate`, `--no-self-finalize`, `--no-isolate-worktree`, `selectors`, `--run-id`, `--retry-incomplete` |
| OC-ONLY | 7 | `--agent`, `--audit`, `--auto`, `--opencode`, `--variant`, `--verify`, `--verify-with` |
| AGY-ONLY | 10 | `--agy`, `--agy-executable`, `--dangerous`, `--dangerously-skip-permissions`, `--effort`, `--new-session`, `--no-audit`, `--no-dangerously-skip-permissions`, `--no-verify`, `--timeout` |

Of the 17 shared, the TWELVE spec-governed run-policy rows are ALREADY registered from one place
(`runner_shared.register_run_policy_flags`, called twice per host), which is F-3 and is correct. So the
de-duplication payoff of a shared core is the four subparser skeletons plus a handful of byte-identical
`--repo`/`run_id`/`--json` registrations, and the cost is parameterizing 17 host-specific option strings
plus roughly 8,400 characters of oc help text and 5,100 of agy's (50 and 41 percent of each function's
source).

AND ONE DIFFERENCE IS NOT A STRING BUT AN INCOMPATIBLE CONTRACT: `--no-verify` resolves to dest
`validate` on oc and dest `no_verify` on agy, while `--verify`/`--audit` exist only on oc. agy defends this
with a build-time guard (`assert_verification_flags_are_distinct`, `agy_runipd.py:1959`) whose docstring
records that registering oc's alias list would make `BooleanOptionalAction` auto-generate
`--no-verify`/`--no-audit` and, under `conflict_handler="resolve"`, silently STEAL agy's shipped spellings.
The Set's oc-preferred ruling therefore cannot be applied to this symbol.

THE COUNTERVAILING GOOD NEWS, which makes this the most mechanically executable of the five: the closure
is the cleanest in the Set (7 free module-level names, only TWO still double-defined,
`_add_output_mode_flags` and `_detect_driver_command`; `ACTION_CHOICES` and `DEFAULT_STALL_TIMEOUT` are
equal constants), and there are ZERO source-inspection pins on `build_parser`, because all 31 test files
that touch it call `build_parser()` and assert on the PARSER OBJECT. So unlike every sibling, a relocation
here breaks no pin.

So the honest goal for THIS plan, pending OQ-03, is: MEASURE the flag surface and the closure, PIN the
per-host flag contract including the verification-dest asymmetry, DELIVER the analysis of whether a shared
core adds anything given that the shared half is already shared, and GUARD what was measured.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

SCOPE GATE ADDED AT REVIEW 2026-09-16. E-01, E-02, E-03 and E-05 are authorized unconditionally: they
measure, they pin the per-host flag contract, they enumerate what is already shared, and they guard what was
measured. THE SPLIT ITSELF IS GATED on OQ-03, which is `Blocking: yes`; E-04 delivers the ANALYSIS the
decision needs and performs no relocation.

### Task group 1: measure before touching

- [x] E-01 MEASURE THE FLAG SURFACE AND THE CLOSURE at execution HEAD, and refuse to proceed to E-04 on a stale list. TWO measurements, because the line count is the wrong unit for a parser. (a) Enumerate every `add_argument` option string on BOTH hosts across all four subparsers and classify each as shared / oc-only / agy-only; the Goal table records 17 / 7 / 10 at review. Additionally record, per host, the DEST each of `--validate`, `--no-validate`, `--verify`, `--no-verify`, `--audit`, `--no-audit` resolves to, because that is where the incompatible contract lives (F-7). (b) Run the closure test on `oc_runipd.build_parser`; the Goal table records 7 free names with only TWO still double-defined. This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: both tables reproduced at execution HEAD; the 17/7/10 partition stated with members; the six verification-flag dests stated per host; the still-double-defined count stated; the ZERO-pin fact (F-9) confirmed or refuted by a repo-wide search for source inspection of `build_parser`.
  - Execution state: performed

- [x] E-02 PIN THE PER-HOST FLAG CONTRACT, which is what F-2's hazard actually requires and which no existing test states per host. Assert, for BOTH hosts, that the exact set of option strings each subparser registers is UNCHANGED (a table in the test, so an addition or removal fails), and assert the verification-dest asymmetry DIRECTLY: on oc `--verify`/`--audit`/`--no-verify` all resolve to dest `validate`; on agy `--verify`/`--audit` do NOT exist and `--no-verify`/`--no-audit` resolve to dest `no_verify` while `--validate`/`--no-validate` resolve to `validate`. Then add the characterization tests the parent's constraint requires. Prefer PARSER-OBJECT assertions over source inspection, following the 31 existing behavioral callers rather than introducing a pin this function has never had (F-9). This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed suite that passes against UNMODIFIED code and FAILS if any host's flag set or any verification dest moves; agy's build-time guard `assert_verification_flags_are_distinct` still invoked and still passing.
  - Execution state: performed

### Task group 2: what is already shared

- [x] E-03 ENUMERATE WHAT IS ALREADY SHARED, so the split's actual payoff is a measured number rather than an assumption. F-3 is correct that `runner_shared.register_run_policy_flags` already registers the 12 spec-governed `RUN_POLICY_FLAGS` rows and is called twice per host; state that, and state what REMAINS genuinely duplicated after accounting for it (measured at review: the four subparser skeletons, and the byte-identical `--repo`/`run_id`/`--json` registrations on `status`/`report`). Also state the STRING VOLUME the split would have to parameterize: roughly 8,400 characters of help/description text on oc and 5,100 on agy, 50 and 41 percent of each function's source. Do NOT edit product code in this item.
  - Depends on: E-01
  - Expected outcome: a written accounting of the residual duplication, with the payoff of a shared core stated as a number of lines rather than implied by the 47-line diff.
  - Execution state: performed

### Task group 3: the split, GATED

- [x] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01 through E-03: (a) the residual payoff from E-03 against the cost of parameterizing 17 host-specific option strings and 13,500 characters of help text; (b) that the oc-preferred ruling CANNOT apply, with the `assert_verification_flags_are_distinct` docstring quoted, since adopting oc's aliases would collide with agy's shipped `--no-verify`; (c) whether `_add_output_mode_flags` should move here, given child 04 assigns it to child 03 and child 03 as re-scoped does not lift it, so it is currently ORPHANED between two plans; and (d) a route recommendation with the reason. Change no runner logic in this item.
  - Depends on: E-01, E-03
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement, explicitly answering whether a parser whose shared half is already shared warrants a shared core.
  - Execution state: performed

### Task group 4: proof

- [x] E-05 Add `tests/test_rununify_build_parser.py` asserting WHAT THIS PLAN ACTUALLY DID, driven by a named table rather than by the aspiration: the 17/7/10 flag partition asserted per host, the six verification dests asserted per host, the closure classification asserted, and `_add_output_mode_flags` / `_detect_driver_command` asserted STILL double-defined (the inverse assertion, so a later agent cannot collapse either without the OQ-03 decision). If OQ-03 authorizes the split, extend this file with shared-core object identity and the repo-wide AST anti-re-fork scan (per the parent's F10, not a pairwise check); do NOT write those assertions while the split is ungated, because a test asserting a state the code is not in is a failing test, not a guard.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a suite that fails if any host's flag set changes, if a verification dest moves, or if a pinned double definition is unilaterally collapsed; and that does NOT assert an unexecuted split.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic and imports no runner, so it
  can hold the core without a cycle. It already uses NAME/VALUE INJECTION for exactly this shape
  (`run_checked(..., env_builder=)`, `save_state(..., write_report=)`, `resume_via_launcher(launcher, ...)`),
  which is the pattern the hook should follow rather than a new mechanism.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` forbids a runner-to-runner
  import, so the core must land in `runner_shared` and never be reached by importing the other host.
  CORRECTED AT REVIEW: that guard is a SUBSTRING check for `"import oc_runipd"` /
  `"import agy_runipd"` (`tests/test_review_findings_cascade.py:308-313`), which agy's
  `from agent_workflows.oc_runipd import (...)` form does not match; agy uses it ten times. The rule that
  does hold is `runner_shared`'s own, asserted by AST at `tests/test_runner_shared.py:955`. It happens not
  to matter for THIS symbol, since none of `build_parser`'s closure names crosses between runners.
- ZERO SOURCE-INSPECTION PINS EXIST ON `build_parser`, uniquely among the five large functions (against 14
  for `execute_item` and 11 for `initialize_run`). All 31 test files that touch it call `build_parser()` and
  assert on the PARSER OBJECT. So a relocation here breaks no pin, and E-02 should keep it that way by
  asserting on the parser rather than introducing the first source pin this function has ever had.
- `runner_shared.register_run_policy_flags` ALREADY registers the 12 spec-governed `RUN_POLICY_FLAGS` rows
  and is called TWICE per host (once for `start`, once for `resume`). This is F-3 and it is correct: that
  half is already single-implementation and must not be re-forked.
- `agy_runipd.assert_verification_flags_are_distinct` (`:1959`) is a BUILD-TIME guard agy calls at the end
  of its `build_parser` and oc does not have. It asserts `--validate`/`--no-validate` -> `validate` and
  `--no-verify`/`--no-audit` -> `no_verify`. Its docstring records the measured hazard: registering oc's
  alias list on agy makes `BooleanOptionalAction` auto-generate `--no-verify`/`--no-audit`, which under
  `conflict_handler="resolve"` SILENTLY STEALS agy's shipped spellings. Preserve the call and the guard.
- HALF THIS FUNCTION IS PROSE. Measured: 8,376 of oc's 16,443 source characters and 5,051 of agy's 12,227
  are string literals (help, description, epilog). Any "shared core" must either parameterize that text or
  impose one host's help on the other, and the latter is an operator-visible change.
- The parent Set forbids a child changing what a runner DOES, and forbids reconciling a symbol the
  characterization baseline has not pinned. E-01 exists to satisfy the second constraint.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | `build_parser` is the MOST host-specific of the five by share: 23 of 47 changed lines carry a host token, because half its content IS the host's own CLI surface (its binary name, its help text, its host-only flags). **CONFIRMED AT REVIEW AND UNDERSTATED, and this finding is RIGHT while the Concern above it is wrong.** Measured: 47 differing lines out of 46 oc and 47 agy TOTAL normalized lines, similarity 0.4946, the LOWEST of the five large functions (`initialize_run` 0.9345, `execute_item` 0.851, `run_queue` far higher still). Flag-by-flag: 17 shared option strings, 7 oc-only, 10 agy-only. And 50 percent of oc's source characters are string literals (41 percent on agy). So this function is not "mostly drift with a host-specific share"; it is two different CLI contracts that agree on a spec-governed core which is ALREADY shared. |
| F-2 | HIGH | `build_parser`, both hosts | THE HAZARD THIS SPLIT CARRIES: `tests/test_run_flag_surface.py` reads spec `25kzda` 2.1 as a FILE in BOTH directions, so a flag registered without being declared in the spec (or vice versa) turns the suite red. This plan must not add, remove, or rename a single operator-visible flag. |
| F-3 | MED | `build_parser` | DIFFERENCE, the shared run-policy flags: `runner_shared.RUN_POLICY_FLAGS` already exists as the single spec-governed flag table both hosts register from, so that half is ALREADY unified and must not be re-forked. **VERIFIED EXACTLY: 12 rows in `RUN_POLICY_FLAGS`, and `register_run_policy_flags` is called TWICE per host (`start` and `resume`).** This is the finding that decides the plan's economics: it means the spec-governed half of the shared surface is already single-implementation, so a shared core's remaining payoff is only the four subparser skeletons and a few byte-identical registrations. E-03 now quantifies that residue. |
| F-4 | MED | `build_parser` | DIFFERENCE, host-only flags: oc has `--opencode`, agy has its own binary override. These stay host-side. **MEASURED AND FAR LARGER THAN TWO FLAGS: 7 oc-only and 10 agy-only option strings.** oc-only: `--agent`, `--audit`, `--auto`, `--opencode`, `--variant`, `--verify`, `--verify-with`. agy-only: `--agy`, `--agy-executable`, `--dangerous`, `--dangerously-skip-permissions`, `--effort`, `--new-session`, `--no-audit`, `--no-dangerously-skip-permissions`, `--no-verify`, `--timeout`. Several reflect capabilities rather than names: `--variant`/`--agent`/`--verify-with` belong to oc's runner-profile subsystem (zero `runner_profiles` references in agy), and `--effort`/`--timeout`/`--dangerously-skip-permissions` are agy CLI concepts oc has no analogue for. "These stay host-side" is right; the count is 17, not 2. |
| F-5 | MED | `build_parser` | DIFFERENCE, help/usage text: host names throughout; supplied by child 04's descriptor. **UNDERSTATED BY AN ORDER OF MAGNITUDE, and a descriptor cannot carry it.** Measured: 8,376 of oc's 16,443 source characters and 5,051 of agy's 12,227 are string literals, so 50 and 41 percent of each function IS help text. It is not "host names throughout": oc's description documents the `as <profile>` positional clause, per-field precedence, and profile freezing (a subsystem agy lacks entirely), while agy's documents clean-session skeptical self-validation. A host-name substitution cannot turn one into the other. Any shared core must parameterize the whole text or impose one host's help on the other, and the latter is an operator-visible change the plan forbids itself. |
| F-6 | BLOCKER | the Concern; measured at HEAD `7936c13d` | **THE CONCERN'S CONCLUSION IS FALSE AND CONTRADICTS THIS PLAN'S OWN F-1.** "Most of the divergence is DRIFT in shared logic rather than genuine host specificity" is the standard sentence from the other four split children, and here the measurement refutes it: 47 differing lines out of 46/47 total, similarity 0.4946, 17 host-specific option strings against 17 shared of which 12 are already shared. F-1 says the opposite and F-1 is correct. An executor reading the Concern would look for drift to reconcile and find two intentionally different CLI contracts. |
| F-7 | BLOCKER | `agy_runipd.py:1959-1990`; live dest inspection | **ONE DIFFERENCE IS AN INCOMPATIBLE CONTRACT, NOT A STRING, AND THE OC-PREFERRED RULING CANNOT APPLY.** Measured live: on oc, `--verify`, `--audit` and `--no-verify` ALL resolve to dest `validate`; on agy, `--verify`/`--audit` DO NOT EXIST and `--no-verify`/`--no-audit` resolve to dest `no_verify` while `--validate`/`--no-validate` resolve to `validate`. agy defends this with a BUILD-TIME guard, `assert_verification_flags_are_distinct`, called at the end of its `build_parser` and absent from oc. That guard's docstring records the measured hazard verbatim: registering oc's alias list on agy makes `BooleanOptionalAction` auto-generate `--no-verify`/`--no-audit`, which with the default handler raises at build time and with `conflict_handler="resolve"` does something "far worse and SILENT: the new action STEALS `--no-verify`/`--no-audit`, and the shipped spelling stops meaning what every existing invocation and every piece of documentation says it means". So "resolve to oc unless a difference is a real capability" cannot be applied: adopting oc's aliases BREAKS agy's shipped CLI. This is an A / NOT-A case needing a per-symbol maintainer decision. |
| F-8 | HIGH | `Item-Dependencies: executed:tx6q0h`; child 03 and child 04 scopes | **`_add_output_mode_flags` IS ORPHANED BETWEEN TWO SIBLING PLANS.** Of the only TWO still-double-defined closure names, child 04 (`tx6q0h`) lifts `_detect_driver_command` and EXPLICITLY assigns `_add_output_mode_flags` to child 03 ("which is child 03's and is display-only"), while child 03 (`i3d6ml`) was re-scoped at its own review from 48 symbols to 9 and does NOT lift it. So the declared prerequisite clears one of two, and the second is currently owned by nobody. Also worth the maintainer's attention: `tx6q0h` is itself `reviewed`/`no-go` with its own blocking question, so this edge points at a plan that cannot currently execute. |
| F-9 | HIGH | repo-wide search of `tests/` | **A GOOD FINDING THE PLAN DOES NOT CLAIM: THERE ARE ZERO SOURCE-INSPECTION PINS ON `build_parser`.** Measured across all `tests/test_*.py`: zero `inspect.getsource(...build_parser)`, zero AST-lookup-by-name, zero `split("def build_parser")`. Thirty-one test files call `build_parser()` and assert on the PARSER OBJECT. That is unique among the five large functions (`execute_item` carries 14 such pins, `initialize_run` 11) and it means a relocation here breaks no pin. E-02 must PRESERVE that property by asserting on the parser rather than introducing the first source pin this function has ever had. |
| F-10 | HIGH | closure measured at HEAD | **A SECOND GOOD FINDING: THE CLOSURE IS THE CLEANEST IN THE SET.** `build_parser` closes over only SEVEN module-level names: three module handles (`argparse`, `runner_shared`, `runner_stop`, all already single objects), two equal constants (`ACTION_CHOICES` = `('review','plan','execute')` and `DEFAULT_STALL_TIMEOUT` = 600.0, identical on both hosts), and only TWO still double-defined (`_add_output_mode_flags`, `_detect_driver_command`). Compare `execute_item`'s 18 and `initialize_run`'s 8-plus-`__file__`. So the mechanical obstacle that blocks the other split children is nearly absent here; what blocks THIS one is that the content is genuinely host-specific (F-6, F-7). |
| F-11 | MED | E-02/E-03/E-04 right-sizing as authored | The original E-02 bundled the relocation, 17 flag-string decisions, 13,500 characters of help-text parameterization and the verification-dest collision into one pass, which the count-based lint cannot see. The re-scoped items are two measurements, one flag-contract pinning suite, one residual-payoff accounting, one written analysis, and one guard suite: one focused pass each. |
| F-12 | LOW | `tests/test_run_flag_surface.py` | The plan names this suite in F-2 but did not FENCE it, and E-02's flag-contract assertions may most naturally extend it rather than a new file (it already reads spec `25kzda` 2.1 as a FILE in both directions and holds 89 tests, green at review). Added to `Scope-Paths` so the declaration is honest whether or not the executor edits it. |

## Proposed changes (ordered, validatable)

1. Measure the flag surface (17/7/10) and the closure (7 names, 2 double-defined) at execution HEAD,
   including the six verification-flag dests per host (E-01).
2. Pin the per-host flag contract and the verification-dest asymmetry, on the PARSER OBJECT rather than
   by source inspection (E-02).
3. Account for what is ALREADY shared, so the split's residual payoff is a number (E-03).
4. Record the split analysis as a DELIVERABLE for OQ-03 rather than performing it (E-04).
5. Add the guard suite for what was measured, including the inverse assertions (E-05).

## Deferred / out of scope (with reason)

- The other four large functions of this Set, each owned by its own sibling child, because each is a
  distinct seam and the parent forbids a child exceeding one cohesive seam.
- The 48 no-disagreement symbols (child 03), the 8 host-string symbols (child 04), the two behavior
  conflicts (child 05), and the record type (child 06). All are ordered BEFORE this plan so their
  results are available rather than re-derived. CORRECTED AT REVIEW: child 03 was re-scoped to 9 symbols and
  child 04 to 6, and between them `_add_output_mode_flags` is now owned by NEITHER (F-8), so one of this
  plan's two remaining double definitions has no upstream owner.
- THE SPLIT ITSELF, deferred to OQ-03 rather than attempted. Stated plainly because a reader will otherwise
  assume it was forgotten: the shared half is already shared (F-3), the unshared half is 17 host-specific
  option strings plus 13,500 characters of divergent help text (F-4, F-5), and one difference is an
  incompatible contract the oc-preferred ruling cannot resolve (F-7).
- ADOPTING OC'S VERIFICATION ALIASES ON AGY, because it would collide with agy's shipped `--no-verify` and
  is exactly what `assert_verification_flags_are_distinct` exists to prevent (F-7). This is an A / NOT-A
  case folded into OQ-03(b), not a difference this plan may resolve.
- Any behavior change, feature addition, or flag change. This plan as re-scoped changes NO product code:
  every item measures, pins, accounts, analyses, or guards.

## Scope check

- Over-scope: none. As re-scoped this plan writes tests and analysis only; it modifies no product module.
  `tests/test_run_flag_surface.py` is declared because E-02's flag-contract assertions may extend it rather
  than a new file, and because it is the suite F-2's hazard would break first (F-12).
- Under-scope: this plan does not perform the split it is named for. That is deliberate and gated (OQ-03),
  not an omission: E-04's deliverable is the analysis the maintainer needs, and E-03's residual accounting is
  what makes the cost/benefit decidable. It also does not attempt to shrink `build_parser`, which remains a
  legitimate later refactor.

## Required tests / validation

1. E-01's TWO tables, reproducible: the flag partition per subparser (17 shared / 7 oc-only / 10 agy-only at
   review, with members) and the closure classification (7 free names, 2 double-defined), each with the
   command that produced it and the HEAD. Plus the six verification-flag dests per host.
2. E-02's flag-contract suite, green against UNMODIFIED code: each host's exact option-string set per
   subparser, and the verification-dest asymmetry asserted DIRECTLY (oc: `--verify`/`--audit`/`--no-verify`
   all -> `validate`; agy: `--verify`/`--audit` absent, `--no-verify`/`--no-audit` -> `no_verify`,
   `--validate`/`--no-validate` -> `validate`). Assert on the PARSER OBJECT, not on source text (F-9).
   Plus the characterization tests for the branches a split would move, with the previously uncovered agy
   branches named. Both hosts' existing suites alone are NOT sufficient, because the parent measured them
   as asymmetric (95 oc tests versus 21 agy at the time).
3. `tests/test_run_flag_surface.py` green, by name, before and after every item. Measured at review:
   `python3 -m pytest tests/test_run_flag_surface.py -o addopts=""` gave `89 passed`. This is the suite that
   reads spec `25kzda` 2.1 as a FILE in both directions and is F-2's hazard made executable.
4. AGY'S BUILD-TIME GUARD still invoked and still passing: `agy_runipd.build_parser()` must continue to call
   `assert_verification_flags_are_distinct(start)`, and constructing the parser must not raise. A test that
   merely imports the module does NOT establish this; build the parser.
5. E-03's residual-payoff accounting, with the shared-already count and the string-volume figures stated as
   numbers.
6. `tests/test_rununify_build_parser.py` (new): the flag partition asserted per host; the verification dests
   asserted per host; the closure classification asserted; `_add_output_mode_flags` and
   `_detect_driver_command` asserted STILL double-defined.
7. NON-VACUITY, BIDIRECTIONAL. Two controls, both pasted. (a) Add a throwaway flag to one host's parser in a
   scratch copy and show the new suite FAILS naming it; restore. (b) Change the agy verification-dest
   assertion to expect oc's mapping and show it FAILS, proving the suite would catch the F-7 collision;
   restore. A guard that only fails one way does not pin a boundary.
8. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green.
9. Bare `python3 -m pytest`, summary pasted, no new failure against a baseline taken at YOUR OWN HEAD before
   changing anything. Sibling `i3d6ml`'s review measured a load-dependent timeout that passes in isolation,
   so reproduce any single failure against the pre-change baseline before attributing it here.

## Spec / documentation sync

No `.spec.md` change expected: this is an internal refactor with no operator-visible contract change. IF
execution finds that a spec sentence describes the divergence being removed, amend it in the SAME change
and add the spec path to `Scope-Paths`, per the repository's spec-amendment rule.

REVIEWED 2026-09-16 AND THIS IS THE MOST SPEC-COUPLED OF THE FIVE SPLIT CHILDREN, so the boilerplate needs
sharpening. `build_parser` IS the surface spec `25kzda` 2.1 governs, and
`tests/test_run_flag_surface.py:43-48` reads
`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` as a FILE, extracting its
grammar block and failing in BOTH directions: a flag the spec declares but the code does not register fails,
and a registered flag the spec does not declare fails, with an exclusion list where "silence is a failure".
Consequences. FIRST, adding or renaming ANY option string here forces a spec amendment in the same change,
with the spec path in `Scope-Paths`. As re-scoped this plan registers nothing, so it forces none. SECOND, if
OQ-03 chooses route (C) (grow `RUN_POLICY_FLAGS` instead of relocating the function), each new row IS a spec
change by construction and must arrive with the amendment. THIRD, the per-host asymmetry F-7 documents may
not be described in the spec at all, since that suite checks the surface against the SPEC rather than
per host; E-04 should say whether the spec acknowledges that `--no-verify` means different things on the two
hosts, because if it does not, the spec is currently incomplete and that is worth reporting even though
fixing it is not this plan's job.

ANSWERED AT EXECUTION 2026-09-17, AND THE ANSWER IS NO. `NO .spec.md FILE WAS CHANGED BY THIS PLAN`, which
is correct: as re-scoped it registers no flag, so it forces no amendment. But the third consequence above was
checked and the spec IS incomplete. Spec `25kzda` 2.1's grammar block declares neither `--validate` nor
`--verify` nor `--no-verify`; only the twelve `RUN_POLICY_FLAGS` rows are spec-governed, which is why
`tests/test_run_flag_surface.py` structurally CANNOT see the F-7 asymmetry (it checks the surface against the
SPEC, in both directions, for the flags the spec declares). The runner `--no-verify` appears in the spec only
in Section 2.1's 2026-09-05 amendment note and the `RUN-COMMIT-GATEWAY` rows, and there only to separate the
RUNNER sense from the GIT sense. Nothing states that the flag means `--no-validate` on agy and is an alias of
`--validate`'s tri-state on oc, nor that `--verify`/`--audit` do not exist on agy at all. So a live, shipped,
operator-visible per-host difference is undocumented, and a future de-duplication has no spec sentence to
check itself against. REPORTED RATHER THAN FIXED, per this section's own instruction, and filed as backlog
`xdgorn` so it has a durable carrier instead of living in plan prose.

## Open questions

### OQ-01: Where exactly does the hook boundary belong?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: At the points Findings names as genuinely host-specific, and nowhere
  else. The test is mechanical rather than aesthetic: if a candidate boundary would require the shared
  core to contain an `if host == ...` branch, the boundary is in the wrong place, because that branch is
  the duplication this Set exists to remove wearing a different shape.

### OQ-02: What if the split cannot be done without changing behavior?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: STOP AND REPORT rather than proceeding. The parent's hard constraint
  is that a child may not change behavior, and E-02's characterization suite is what makes a violation
  visible instead of silent. A partial split that leaves a smaller shared core is an acceptable outcome
  and is strictly better than a complete split that moves behavior; say which branches were left behind
  and why. CONFIRMED AT REVIEW 2026-09-16, AND THE CONDITION HAS OCCURRED. F-7 is the clearest case in the
  entire Set: adopting oc's version of the verification flags would BREAK agy's shipped CLI, and agy already
  carries a build-time guard whose whole purpose is to make that failure loud. F-5's help-text volume is the
  second case, since imposing one host's description on the other is an operator-visible change. So the
  re-scope below is this plan obeying its own instruction.

### OQ-03: The shared half is already shared and one difference is an incompatible CLI contract. Is a shared `build_parser` worth having?

- Blocking: yes
- Finding: PR-001, PR-002
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-16, and the answer is ROUTE (A)
  AS THE OBJECTIVE, with the route's stated obstacles ruled to be work rather than blockers. The
  maintainer's directive, given directly: "at the end of the SET, there should be one code base shared
  by the two runners that contains 100% of the otherwise redundant code that currently is duplicated
  between the two runners." So DO THE SPLIT. Routes (C) and (D) are refused: both leave this function
  duplicated, which the directive forbids. Route (B)'s re-ordering is PERMITTED as a tactic (see below)
  but is not itself the answer, because it defers rather than achieves.
  THE TWO OBSTACLES THIS QUESTION RESTED ON WERE BOTH RULED ON DIRECTLY, and both dissolve:
  (1) TESTS ARE NOT IMMOVABLE. Asked whether the source-reading pins prevent this work, the maintainer's
  answer was that they do not, and this repository has ALREADY adapted such a guard for shared code:
  `tests/test_nested_tty_noninteractive.py:190-203` counts the shared file's launch sites toward BOTH
  runners, its docstring records why, and all 41 tests in that file plus `tests/test_lane_tool_identity.py`
  pass at this HEAD. A source-reading pin is therefore something to UPDATE DELIBERATELY as part of the
  work: re-base it on the code's new location, record what it now asserts, and prove it still catches the
  regression it was installed for (an injected-regression test, which several of these pins already have).
  WHAT REMAINS FORBIDDEN is WEAKENING a guard silently, i.e. lowering a threshold or deleting an assertion
  so a failure disappears. Re-basing is not weakening. Where a pin asserts the ORDER of safety gates, the
  ordering property must survive the move; assert it on the shared implementation, and if a behavioral
  assertion can replace a source-text one without losing coverage, prefer it and say so.
  (2) THE INJECTED-DEPENDENCY COUNT IS NOT A VETO, AND THE MECHANISM IS ALREADY RULED. This question
  treated N injected parameters as a reason to stop, and cited the maintainer's 2026-09-03 `818uru`
  OQ-02 ruling as being against it. That reads the ruling backwards. The ruling ESTABLISHED the
  mechanism to use: `runner_shared` owns the real function taking each outside dependency as an explicit
  PARAMETER, and each runner keeps a ONE-LINE wrapper at the ORIGINAL name and ORIGINAL signature that
  binds its own dependency (see the executed plan's E-02 note). What that ruling rejected was threading a
  parameter through ~86 CALL SITES, which the wrapper form specifically avoids. So a shared core with N
  parameters plus a thin per-host wrapper IS the sanctioned form, not a violation of it.
  (3) SIBLING COUPLING IS NOT A BLOCKER EITHER. The maintainer confirmed directly that many functions may
  be de-duplicated together before testing, so a dependency that is still double-defined because a SIBLING
  has not landed is to be handled by doing the work in dependency order within the Set, not by refusing.
  Where this plan's dependency count falls materially once a sibling lands, run in that order (route (B)'s
  tactic) and say so in the execution note; where it does not, inject and wrap per (2).
  HOW TO SEQUENCE, since every one of these five children asked the same question: the runner already
  sorts by dependency depth and re-checks dependencies at dispatch, so declared `Item-Dependencies` are
  sufficient to order the work. Do not re-order plans by hand.
  THE ORIGINAL REVIEWER'S MEASUREMENT BELOW IS PRESERVED and E-01 must reproduce it at execution HEAD;
  only its CONCLUSION (that a route decision was owed by the maintainer) is superseded.
  --- original analysis, superseded as to its conclusion ---
  NOT DECIDED, deliberately. Unlike the other four split children, the
  question here is not "can this be done" (mechanically it is the EASIEST of the five) but "should it",
  which is a design call the maintainer owns.
  THE MEASUREMENT, not an opinion. `build_parser` has the LOWEST similarity of the five large functions
  (0.4946) and the CLEANEST closure (7 free names, 2 still double-defined) and ZERO source-inspection pins.
  Its flag surface is 17 shared option strings against 17 host-specific ones (7 oc-only, 10 agy-only), and
  TWELVE of the 17 shared are ALREADY registered from one place through
  `runner_shared.register_run_policy_flags`. Half of each function by character count is help text that
  documents different capabilities (oc's `as <profile>` precedence chain; agy's clean-session validation).
  And `--no-verify` maps to dest `validate` on oc and `no_verify` on agy, an incompatibility agy defends
  with a build-time guard (F-7).
  FOUR ROUTES, with what each costs. (A) SHARE THE WHOLE PARSER, parameterizing 17 option strings and
  13,500 characters of help text: mechanically feasible (the closure is clean and no pin blocks it) and the
  result is a template whose entire visible output is caller-supplied, for a residual payoff of four
  subparser skeletons. (B) SHARE THE SKELETON ONLY: one shared helper that creates the parser and the four
  subparsers with the byte-identical `--repo`/`run_id`/`--json` registrations, each host then adding its own
  flags and its own help; small, honest, and its payoff is exactly the residue E-03 measures. (C) EXTEND THE
  EXISTING MECHANISM INSTEAD: `register_run_policy_flags` already proves the right pattern for this
  function, so any further sharing should add ROWS to a spec-governed table rather than relocate the
  function; this is arguably what the Set should have asked for here. (D) DO NOT SHARE `build_parser`: a
  host's CLI surface is its public contract, the spec-governed part is already shared, and the remaining
  duplication is four `add_parser` calls.
  RECOMMENDATION: (C), with (D) as the honest fallback. (C) is recommended because the repository already
  contains the working precedent (12 spec-governed rows, one registration function, a contract test that
  reads the spec as a FILE in both directions), so growing that table is how a future shared flag should
  arrive, whereas relocating the function adds a second mechanism for the same job. (A) is not recommended.
  Note that (D) here is a much stronger position than for the sibling children, because the duplication
  being tolerated is genuinely small and genuinely host-specific.
  THIS PLAN'S E-01 THROUGH E-05 ARE EXECUTABLE UNDER EVERY ROUTE, including (D), and E-02's per-host flag
  contract plus the F-7 dest assertions are worth landing regardless: no existing test states the two
  hosts' flag sets per host, and `test_run_flag_surface.py` checks the surface against the SPEC rather than
  against each host's own shipped set.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: BOTH tables pasted with the commands that produced them and the HEAD. (a) The flag partition per subparser with every option string classified, counts compared against the 17 / 7 / 10 measured at review. (b) The six verification-flag dests per host, showing oc's three-to-one collapse and agy's split. (c) The closure classification of all 7 free names with the still-double-defined pair named. (d) The repo-wide search confirming or refuting ZERO source-inspection pins on `build_parser` (F-9). A table that repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence: Execution HEAD `4a1bb873e68d8c5a52a3c735a1d5a04c2ef11adf`. Every number below was RE-DERIVED here, not copied from the review.

    **(a) THE FLAG PARTITION, AND THE ONE NUMBER THAT MOVED.** The review's 17 / 7 / 10 REPRODUCES EXACTLY, but only by the method that produced it, and that method is not what an operator meets. Both are now measured and both are pinned.

    METHOD A, the LIVE parser objects (`measure_e01a.py`, all five subparsers on both hosts):

    ```
    === subparsers per host ===
    oc: ['report', 'resume', 'start', 'status', 'stop']
    agy: ['report', 'resume', 'start', 'status', 'stop']

    --- subparser `start` ---
      shared   (44): [...]
      oc-only  ( 8): ['--agent', '--audit', '--auto', '--no-auto', '--opencode', '--variant', '--verify', '--verify-with']
      agy-only ( 8): ['--agy', '--agy-executable', '--dangerous', '--dangerously-skip-permissions', '--effort', '--new-session', '--no-dangerously-skip-permissions', '--timeout']
    --- subparser `resume` ---
      shared   (33): [...]
      oc-only  ( 8): ['--audit', '--no-audit', '--no-validate', '--no-verify', '--validate', '--variant', '--verify', '--verify-with']
      agy-only ( 2): ['--agy', '--agy-executable']
    --- subparser `report` ---  shared (4), oc-only 0, agy-only 0
    --- subparser `status` ---  shared (5), oc-only 0, agy-only 0
    --- subparser `stop`   ---  shared (8), oc-only 0, agy-only 0

    === WHOLE-CLI UNION PARTITION ===
    counts: shared=51 oc-only=8 agy-only=8
    ```

    METHOD B, the review's SOURCE-LITERAL count (`measure_e01c.py`), which cannot see a `--no-X` that `BooleanOptionalAction` auto-generates nor anything a shared helper registers:

    ```
    oc: 37 literals, 24 distinct
    agy: 37 literals, 27 distinct
    SHARED   (17): ['--action', '--json', '--manifest', '--max-items-per-session', '--model', '--no-isolate-worktree', '--no-self-finalize', '--prepare-only', '--repo', '--retry-incomplete', '--run-id', '--runbook', '--session', '--stall-timeout', '--validate', 'run_id', 'selectors']
    OC-ONLY  ( 7): ['--agent', '--audit', '--auto', '--opencode', '--variant', '--verify', '--verify-with']
    AGY-ONLY (10): ['--agy', '--agy-executable', '--dangerous', '--dangerously-skip-permissions', '--effort', '--new-session', '--no-audit', '--no-dangerously-skip-permissions', '--no-verify', '--timeout']
    counts (METHOD B): shared=17 oc-only=7 agy-only=10
    ```

    So the review's figure is CORRECT for what it measured and the live figure is 51 / 8 / 8. Both are asserted in `TheFlagPartitionIsPinnedByBothMeasurementMethods`, together with an assertion that the two methods still DISAGREE, so nobody later "fixes" one to match the other. NOTE the trap this exposes: `--no-verify` and `--no-audit` are literal-agy-only but LIVE-SHARED (verified: `--no-audit oc=True agy=True`), i.e. both hosts spell the same flag and mean different things by it, which is exactly (b).

    Also re-derived: raw lines oc=352 agy=266 (review 347/264, drifted by 5 and 2); normalized code lines oc=46 agy=47 (exact); 23 identical, so 23 oc-side and 24 agy-side differ, which is the review's "47" as the SUM of both sides; similarity 0.4946 (EXACT, and the lowest of the five large functions).

    **(b) THE SIX VERIFICATION DESTS PER HOST** (`measure_e01b.py`). oc's three-to-one collapse and agy's split both reproduce:

    ```
    --- `start` ---
      oc : --validate->validate  --no-validate->validate  --verify->validate  --no-verify->validate  --audit->validate  --no-audit->validate
      agy: --validate->validate  --no-validate->validate  --verify->None     --no-verify->no_verify  --audit->None     --no-audit->no_verify
    --- `resume` ---
      oc : --validate->validate  --no-validate->validate  --verify->validate  --no-verify->validate  --audit->validate  --no-audit->validate
      agy: --validate->None      --no-validate->None      --verify->None      --no-verify->None      --audit->None      --no-audit->None
    ```

    A FACT THE REVIEW DID NOT RECORD: on agy `resume`, NONE of the six is registered. That is now pinned by `test_agy_registers_no_verification_flags_on_resume_at_all`, because a shared core registering oc's resume block on both hosts would hand agy six new flags.

    **(c) THE CLOSURE, all 7 free names classified** (`measure_e01c.py`). Exactly as the review recorded, with only TWO still double-defined:

    ```
    free names (7): ['ACTION_CHOICES', 'DEFAULT_STALL_TIMEOUT', '_add_output_mode_flags', '_detect_driver_command', 'argparse', 'runner_shared', 'runner_stop']

      ACTION_CHOICES          oc=True agy=True runner_shared=False  DOUBLE-DEFINED but EQUAL value
      DEFAULT_STALL_TIMEOUT   oc=True agy=True runner_shared=False  DOUBLE-DEFINED but EQUAL value
      _add_output_mode_flags  oc=True agy=True runner_shared=False  DOUBLE-DEFINED
      _detect_driver_command  oc=True agy=True runner_shared=False  DOUBLE-DEFINED
      argparse                oc=True agy=True runner_shared=False  SAME OBJECT (already single)
      runner_shared           oc=True agy=True runner_shared=False  SAME OBJECT (already single)
      runner_stop             oc=True agy=True runner_shared=False  SAME OBJECT (already single)
    ```

    STILL-DOUBLE-DEFINED PAIR NAMED: `_add_output_mode_flags` and `_detect_driver_command`. F-10's "cleanest closure in the Set" is confirmed (against `execute_item`'s 18 and `initialize_run`'s 34).

    **(d) ZERO SOURCE-INSPECTION PINS, CONFIRMED (F-9).** 35 test files touch `build_parser`; a repo-wide search for the pin classes found none:

    ```
    $ grep -rln "build_parser" tests/ | wc -l
    35
    $ grep -rn "getsource" tests/ | grep -i "build_parser"    ->  no matches (exit 1)
    $ grep -rn "build_parser" tests/ | grep -i "ast\.\|getsource\|readlines\|read()\|splitlines"  ->  no matches
    ```

    The only four hits for the name in a mocking context are `mock.patch.object(..., "build_parser", ...)` (`tests/test_oc_runipd_cli.py:158`, `tests/test_oc_runipd.py:4286`, `:4393`), which patch the OBJECT and are not source pins. This property is now itself guarded by `test_build_parser_still_carries_no_source_inspection_pin`, proven non-vacuous in V-05.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: THREE parts, all pasted. (a) The flag-contract suite green, showing each host's exact option-string set per subparser and the verification-dest asymmetry asserted directly. (b) Confirmation the assertions are made on the PARSER OBJECT and that no `inspect.getsource` of `build_parser` was introduced (F-9 preserved). (c) The characterization suite green against UNMODIFIED code with the previously uncovered agy branches named, plus a sabotage of one pinned branch showing the suite FAILS and names it.
  - Observed evidence: **(a) THE FLAG-CONTRACT SUITE GREEN** against UNMODIFIED product code (`git status --porcelain agent_workflows/` empty at the time of the run):

    ```
    $ python3 -m pytest tests/test_rununify_build_parser_characterization.py -o addopts=""
    collected 18 items
    tests/test_rununify_build_parser_characterization.py ..................  [100%]
    ============================== 18 passed in 0.24s ==============================
    ```

    `tests/test_rununify_build_parser_characterization.py` holds three classes. `EachHostRegistersExactlyItsOwnFlagSet` (4 tests) carries `EXPECTED_OPTION_STRINGS`, a per-host per-subparser table of the EXACT option-string set, so an addition or removal fails naming the flag; it also pins the 8/8 host-only partition with members and asserts the table is not stale against the live subparser names. `TheVerificationDestAsymmetryIsPinnedPerHost` (5 tests) asserts the dests DIRECTLY, in both directions: oc's six spellings all resolve to `validate` on BOTH `start` and `resume`; agy's `--verify`/`--audit` are ABSENT, `--no-verify`/`--no-audit` resolve to `no_verify`, `--validate`/`--no-validate` to `validate`; agy's `resume` registers none of the six; agy's build-time guard is called and is non-vacuous; and oc's lack of the guard is asserted as a decision rather than left as an omission.

    **(b) PARSER-OBJECT ASSERTIONS, F-9 PRESERVED.** Every assertion in the new characterization file reaches the parser through `HOSTS[host].build_parser()` and then through the `_SubParsersAction`'s `choices`, `_actions`, `option_strings` and `dest`, or through a parsed `Namespace`. No `inspect.getsource` of `build_parser` was introduced anywhere. This is not merely asserted in prose: `tests/test_rununify_build_parser.py::test_build_parser_still_carries_no_source_inspection_pin` scans EVERY `tests/test_*.py` for the pin classes and passes, and V-05(b) shows it FAILING on a planted pin, so the claim is machine-checked in both directions. (The scanner assembles its needles at runtime so it cannot match its own literals; a hardcoded list made it fail on itself, and excluding the file would have been the wrong fix since this file must be scanned too.)

    **(c) CHARACTERIZATION GREEN, THE PREVIOUSLY UNCOVERED AGY BRANCHES NAMED, AND SABOTAGE.** `TheBranchesASplitWouldMoveAreCharacterized` (9 tests) asserts what each parser PRODUCES, on BOTH hosts wherever the property is shared: a bare `start` freezes the measured defaults (`output_mode=clean`, `verbosity=0`, `stall_timeout=600.0`, `self_finalize=True`, `isolate_worktree=True`); `--quiet`/`--raw` are mutually exclusive; `resume` leaves `verbosity` ABSENT so a frozen tier survives; `--action` choices are constrained; the twelve already-shared policy rows parse identically; and `status`/`report` accept their positional and `--repo`.

    THE AGY BRANCHES THAT HAD NO PER-HOST COVERAGE, now named and pinned by `test_agy_only_start_defaults_are_what_was_measured`: `--effort` (no default; the host decides downstream), `--timeout` (defaults to the module constant `DEFAULT_TIMEOUT = '240m'`), `--new-session` (`False`), and `--dangerously-skip-permissions`, which DEFAULTS TO TRUE. That last one was found by this validation rather than assumed: my first draft asserted `None`, the test failed, and reading the code showed the default is genuinely `True`, which is the opposite of what the flag name suggests and is exactly why it is now pinned with that reason recorded. `test_the_verification_tristate_reads_each_hosts_flags_as_measured` then carries the CONSEQUENCE through `agy_runipd.verification_flag_tristate`, including that `--no-verify --validate` is REFUSED rather than resolved by precedence. Two assumptions of mine were wrong here (`--effort` and `dangerously_skip_permissions`) and both were corrected to the measured truth rather than the test being loosened.

    SABOTAGE, THREE DIRECTIONS, each shown failing and then restored:

    ADDED FLAG (`--throwaway-control-flag` on oc `start`):

    ```
    E  AssertionError: Tuples differ: (['--throwaway-control-flag'], []) != ([], [])
       : oc `start` flag surface CHANGED: added=['--throwaway-control-flag'] removed=[]...
    FAILED ...::test_the_host_only_partition_is_what_was_measured
    FAILED ...::test_every_subparser_registers_exactly_the_measured_option_strings
    ========================= 2 failed, 16 passed in 0.35s =========================
    ```

    REMOVED FLAG (agy `--effort` deleted, the direction an over-eager de-duplication causes):

    ```
    E  + ([], []) : agy `start` flag surface CHANGED: added=[] removed=['--effort']...
    FAILED ...::test_every_subparser_registers_exactly_the_measured_option_strings
    FAILED ...::test_the_host_only_partition_is_what_was_measured
    FAILED ...::test_agy_only_start_defaults_are_what_was_measured
    ========================= 3 failed, 15 passed in 0.41s =========================
    ```

    THE F-7 COLLISION ITSELF is the third direction and is pasted in V-05(b). After each sabotage the file was restored with `git checkout --` / a byte-identical copy and `git status --porcelain agent_workflows/` confirmed EMPTY, then the suite re-run green (18 passed).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the residual-payoff accounting as NUMBERS: how many rows `RUN_POLICY_FLAGS` carries and how many times each host registers them; what remains genuinely duplicated after accounting for that; and the string-literal character counts per host. Plus an explicit statement of the split's remaining de-duplication payoff in lines, so the cost/benefit in OQ-03 rests on a measurement rather than an impression.
  - Observed evidence: All figures from `measure_e03.py` at HEAD `4a1bb873`.

    **WHAT IS ALREADY SHARED, AS NUMBERS.** F-3 is confirmed exactly:

    ```
    RUN_POLICY_FLAGS rows: 12
    flags: ['--allow-mixed', '--allow-drafts', '--unattended', '--full-auto', '--allow-unverifiable',
            '--unverifiable-ok', '--follow-generated', '--with-dependencies', '--retry-budget',
            '--allow-dirty-base', '--integration-retry-limit', '--on-integration-blocked']
    oc: register_run_policy_flags called 2 times in build_parser
    agy: register_run_policy_flags called 2 times in build_parser

    LIVE option strings on `start` attributable to the shared policy table: 21
    SHARED live option strings: 51
      of which already registered from the shared table: 21
      remaining shared strings registered by DUPLICATED code: 30
    ```

    12 rows, 2 registrations per host, accounting for 21 of the 51 shared live option strings. Three further helpers are ALREADY single-implementation or already called from both hosts, measured from each `build_parser`'s call graph: `runner_shared.register_run_policy_flags`, `runner_stop.add_stop_parser` (which supplies the ENTIRE `stop` subparser, 8 option strings, identically on both hosts), plus the two still-forked-but-called `_add_output_mode_flags` and `_detect_driver_command`.

    **WHAT REMAINS GENUINELY DUPLICATED: 23 IDENTICAL NORMALIZED CODE LINES.** This is the payoff figure, and it is stated as a number rather than implied:

    ```
    oc normalized code lines : 46
    agy normalized code lines: 47
    IDENTICAL normalized lines (the de-duplication ceiling): 23
    ```

    The 23, enumerated verbatim by the measurement: the `def` line; `add_subparsers`; four `add_parser` calls (`start`, `resume`, `status`, `report`); two `_add_output_mode_flags` calls; one `register_run_policy_flags` call; `add_stop_parser`; the `return`; and nine byte-identical `add_argument` registrations (`--run-id`, `--no-self-finalize`, `--no-isolate-worktree`, `--max-items-per-session` twice, `--repo` three times, `run_id` twice, `--retry-incomplete`). NOTE THE CORRECTION TO THE REVIEW: it estimated the residue as "the four subparser skeletons plus a handful of byte-identical registrations", which is the right shape but understates it; the measured ceiling is 23 lines, and it is now pinned as `IDENTICAL_NORMALIZED_LINES = 23` so a de-duplication must move it deliberately.

    **THE STRING VOLUME A SHARED CORE MUST PARAMETERIZE:**

    ```
    oc : 8761 string-literal chars / 16829 source chars (52.1%), raw lines=352
    agy: 5195 string-literal chars / 12372 source chars (42.0%), raw lines=266
    ```

    13,956 characters total, 52.1% and 42.0% of each function's source (review: ~8,400/~5,100, 50%/41%; reproduces).

    **THE PAYOFF STATED PLAINLY, so OQ-03's cost/benefit rests on measurement:** relocating this function can remove AT MOST 23 duplicated lines, and doing so requires parameterizing 16 host-specific option strings (8 each way) plus ~14,000 characters of divergent help text whose content documents capabilities the other host does not have (oc's `as <profile>` precedence chain and profile freezing, against zero `runner_profiles` references in agy; agy's clean-session skeptical self-validation). The spec-governed half of the shared surface is already single-implementation, which is what makes the residue small. `test_the_spec_governed_half_is_already_shared_and_must_not_be_re_forked` and `test_the_policy_table_accounts_for_twenty_one_of_the_shared_live_strings` guard the "already shared" half against being silently re-forked by a future "shared core" that would then claim a payoff it did not deliver.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the written analysis, covering parts (a) through (d) E-04 enumerates, with the `assert_verification_flags_are_distinct` docstring quoted as the evidence that the oc-preferred ruling cannot apply, and an explicit disposition for the ORPHANED `_add_output_mode_flags` (F-8). Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence: The full analysis is `.aw/records/walkthroughs/20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md`. It is a TRACKED record rather than a lane note, deliberately: the lane submission tree is gitignored, which is the correction sibling `yrqyxb` had to make after the fact. Summary of each part:

    **(a) RESIDUAL PAYOFF AGAINST COST.** Remove at most 23 duplicated lines; add a parameter surface of 16 host-specific option strings and 13,956 characters of help text. Full numbers in V-03. The analysis also corrects the plan's own Concern: "most of the divergence is DRIFT in shared logic" is FALSE for this symbol (23 identical of 46/47 lines, similarity 0.4946, the lowest of the five), and the plan's own F-1 says the opposite and is correct. An executor trusting the Concern would hunt for drift and find two intentional CLI contracts.

    **(b) THE OC-PREFERRED RULING CANNOT APPLY, WITH THE DOCSTRING QUOTED.** The analysis quotes `assert_verification_flags_are_distinct` (`agent_workflows/agy_runipd.py:2034`) verbatim: "`BooleanOptionalAction` auto-generates a `--no-X` for every option string it is given, so registering `--validate` with oc's alias list (`--verify`, `--audit`) would generate `--no-verify` and `--no-audit`, which this parser already declares. With the default `conflict_handler` that raises at build time and is impossible to miss. With `conflict_handler=\"resolve\"` it does something far worse and SILENT: the new action STEALS `--no-verify`/`--no-audit`, and the shipped spelling stops meaning what every existing invocation and every piece of documentation says it means."

    BOTH BRANCHES WERE EXECUTED RATHER THAN TAKEN ON TRUST, which no prior record in this Set did. The raising branch is pasted in V-05(b). The SILENT branch, reproduced in isolation with `conflict_handler="resolve"`:

    ```
    after resolve-handler theft: namespace = Namespace(validate=False)
    has no_verify attr: False
    --no-verify now resolves to dest: validate
    ```

    `args.no_verify` ceases to EXIST, so agy's freeze site reads `False` unconditionally: verification silently OFF by default on the host whose whole posture is verification ON. This is an A / NOT-A case, not an oc-preferred case.

    **(c) DISPOSITION FOR THE ORPHANED `_add_output_mode_flags` (F-8), STATED EXPLICITLY.** F-8 reproduces: child 04 (`tx6q0h`) lifts `_detect_driver_command` and explicitly assigns `_add_output_mode_flags` to child 03; child 03 (`i3d6ml`) was re-scoped from 48 symbols to 9 (groups A and B) and group H, which holds it, was dropped (verified in `i3d6ml`'s own E-05 text and F-14). DISPOSITION: it should NOT move under this plan, because this plan as re-scoped changes no product code and lifting a shared helper is product code. RECOMMENDED OWNER: child 03, by re-adding group H, since it already owns the lift mechanism and the named-table test pattern; failing that, a new precursor child. Two facts make the lift a decision rather than a move, and both are now pinned: the two bodies genuinely DIFFER (`test_the_two_output_mode_helper_bodies_genuinely_differ`), and the helper carries a deliberate `verbosity_default` asymmetry (0 on `start`, `None` on `resume`) now characterized on BOTH hosts. FILED AS A DURABLE CARRIER: backlog `xw4rb7`, so the orphan does not live only in this prose.

    **(d) ROUTE RECOMMENDATION.** Route (B) as the tactic, with an explicit statement of what route (A) can and cannot mean here. It CAN mean one shared skeleton builder holding the measured 23 lines, each host then adding its own flags and help; that removes the whole measured redundancy, which is what the maintainer's directive asks for. It CANNOT mean one function emitting both hosts' flag surfaces, because those are 16 strings apart and one difference is (b)'s incompatibility; a single function would need either a host branch inside the shared core (the duplication this Set exists to remove wearing a different shape, which this plan's own OQ-01 names as the mechanical test) or a caller-supplied dict of everything host-specific, which reduces the shared core to the skeleton, i.e. to route (B). So route (B) is not a lesser route (A) for this symbol; it is what route (A) resolves to once the verification asymmetry is respected. SEQUENCING: the two closure forks land first, after which the skeleton extraction has no remaining host-specific dependency and, uniquely in this Set, no source pin to re-base. Do not re-order plans by hand; the runner sorts by dependency depth and re-checks at dispatch.

    **NO SPLIT WAS PERFORMED, and OQ-03's status is stated precisely rather than left ambiguous.** OQ-03 is `resolved` ON DISK: the maintainer answered it on 2026-09-16 with a Set-wide directive (100% de-duplication, route (A) as the objective, route (B)'s ordering permitted as a tactic). So this plan did NOT withhold the split pending a decision that was already made. It withheld it for two reasons of AUTHORITY rather than difficulty, both stated in the walkthrough: this plan's own re-scope, written into its E-items and its scope check at review, states that it changes NO product code and that E-04's deliverable is analysis, so performing the extraction would exceed the scope it was approved with; and its declared `Item-Dependencies: executed:tx6q0h` is UNMET at execution HEAD (`tx6q0h` is `approved` in `pending/`, not `executed`), so the one prerequisite the plan names has not landed. Doing the extraction anyway would have meant lifting a symbol another approved plan owns, in a plan whose dependency is unmet, against its own stated scope. WHAT REMAINS FOR THE MAINTAINER IS A SEQUENCING JUDGMENT, and the analysis makes a recommendation on it rather than asking. THE OMISSION CANNOT BE READ AS AN OVERSIGHT BECAUSE IT IS ASSERTED MECHANICALLY: `tests/test_rununify_build_parser.py::TheSplitHasNotBeenPerformed` (5 tests) asserts both hosts still define the function, `runner_shared` does not, the two definitions are not the same object, neither host delegates to its peer, and no source pin has appeared.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FIVE parts, all pasted. (a) `python3 -m pytest tests/test_rununify_build_parser.py -o addopts=""` green, including the inverse still-double-defined assertions. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 7, both directions shown failing and then restored, the second demonstrating the suite would catch the F-7 collision. (c) `tests/test_run_flag_surface.py` green with its count, compared against the 89 measured at review. (d) Proof that `agy_runipd.build_parser()` still calls `assert_verification_flags_are_distinct` and builds without raising. (e) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, plus both hosts' suites green by name.
  - Observed evidence: **(a) THE GUARD SUITE:**

    ```
    $ python3 -m pytest tests/test_rununify_build_parser.py -o addopts=""
    collected 21 items
    tests/test_rununify_build_parser.py .....................                [100%]
    ============================== 21 passed in 1.06s ==============================
    ```

    Five classes. `TheClosureClassificationIsPinned` (5) asserts the closure is exactly the seven measured names, that the three classes are disjoint so the table cannot contradict itself, that the ALREADY_SINGLE names really are one object from both hosts, and that the EQUAL_CONSTANTS agree AND still hold their measured values (so "equal" cannot be satisfied by both hosts drifting together). `TheTwoRemainingForksAreStillForked` (3) is the INVERSE assertion: both forks still defined in both runners, neither in `runner_shared`, and the two `_add_output_mode_flags` bodies genuinely differing. `TheFlagPartitionIsPinnedByBothMeasurementMethods` (3) pins 17/7/10 by literal and 51/8/8 live and asserts the two methods still disagree. `TheResidualDeduplicationPayoffIsMeasured` (5) pins the 23-line ceiling, the 0.4946 similarity, the 52.1%/42.0% string share, and the already-shared policy half in both directions. `TheSplitHasNotBeenPerformed` (5) is the tripwire.

    Both suites together: `39 passed in 1.25s`.

    **(b) NON-VACUITY, BIDIRECTIONAL AND THEN SOME: FIVE controls, each shown failing and then restored.**

    CONTROL 1, THE F-7 COLLISION, which is the control the plan specifically demands. oc's alias list registered on agy, exactly as a naive "resolve to oc" split would:

    ```
    E  argparse.ArgumentError: argument --validate/--no-validate/--verify/--no-verify/--audit/--no-audit:
       conflicting option strings: --no-verify, --no-audit
    FAILED ...::test_agys_build_time_collision_guard_is_still_called_and_still_passes
    FAILED ...::test_agy_splits_the_spellings_across_two_dests_and_omits_two
    FAILED ...::test_agy_registers_no_verification_flags_on_resume_at_all
    (+12 more)
    ========================= 15 failed, 3 passed in 2.67s =========================
    ```

    So the suite WOULD catch the F-7 collision, and the docstring's "raises at build time" branch is now a measured fact. Its SILENT branch is pasted in V-04(b).

    CONTROL 2, AN ADDED FLAG (oc `start`): fails naming `--throwaway-control-flag`. Pasted in V-02(c).

    CONTROL 3, A REMOVED FLAG (agy `--effort`): fails naming `removed=['--effort']`. Pasted in V-02(c).

    CONTROL 4, THE SPLIT LANDING (`runner_shared` acquires a `build_parser`):

    ```
    FAILED ...::TheSplitHasNotBeenPerformed::test_runner_shared_does_not_define_a_build_parser_core
    ========================= 1 failed, 20 passed in 1.18s =========================
    ```

    CONTROL 5, A FORK COLLAPSED PIECEMEAL (agy's `_detect_driver_command` rebound):

    ```
    FAILED ...::TheTwoRemainingForksAreStillForked::test_both_forks_are_still_defined_in_both_runners
    FAILED ...::TheFlagPartitionIsPinnedByBothMeasurementMethods::test_the_live_partition_is_fifty_one_eight_eight
    ========================= 2 failed, 19 passed in 1.31s =========================
    ```

    CONTROL 6, THE ANTI-PIN SCANNER (a real source pin planted in a scratch test file), proving that guard is not vacuous:

    ```
    E  AssertionError: Lists differ: ['test_zz_scratch_pin_control.py: getsource(oc_runipd.build_parser'] != []
    FAILED ...::TheSplitHasNotBeenPerformed::test_build_parser_still_carries_no_source_inspection_pin
    ========================= 1 failed, 20 passed in 1.10s =========================
    ```

    AFTER EVERY CONTROL the sabotage was reverted and `git status --porcelain agent_workflows/` confirmed EMPTY (and the scratch file deleted), with the suites re-run green: `39 passed`.

    **(c) THE SPEC CONTRACT SUITE, MATCHING THE REVIEW'S 89 EXACTLY:**

    ```
    $ python3 -m pytest tests/test_run_flag_surface.py -o addopts=""
    tests/test_run_flag_surface.py ......................................... [ 46%]
    ................................................                        [100%]
    ============================== 89 passed in 5.61s ==============================
    ```

    Also `tests/test_run_flag_surface.py tests/test_runner_shared.py` together: `223 passed in 23.76s`. NOTE: `tests/test_run_flag_surface.py` was declared in `Scope-Paths` and was NOT modified; E-02's assertions landed in the two new files instead, because that suite's job is code-versus-SPEC while this plan's is code-versus-each-HOST. It therefore needs a `--scope-ack`, per the plan's own execution contract which anticipated either outcome and asked which.

    **(d) AGY'S BUILD-TIME GUARD STILL CALLED AND STILL PASSING.** `agent_workflows/agy_runipd.py:5838` still reads `assert_verification_flags_are_distinct(start)` at the end of `build_parser`, and `test_agys_build_time_collision_guard_is_still_called_and_still_passes` BUILDS the parser (a successful build IS the passing guard, since the guard raises `DriverError` on collision) rather than merely importing the module, then additionally proves the guard still REFUSES the collision it was installed for by handing it a deliberately stolen parser. Control 1 above is the end-to-end proof: when the collision is real, building fails.

    **(e) BARE SUITE, NO NEW FAILURE, AGAINST A BASELINE TAKEN AT MY OWN HEAD BEFORE CHANGING ANYTHING.**

    BASELINE, at `4a1bb873` before any edit:

    ```
    $ python3 -m pytest
    31 failed, 7645 passed, 3 skipped, 2 xfailed in 105.51s (0:01:45)
    ```

    AFTER this plan's changes:

    ```
    $ python3 -m pytest
    31 failed, 7684 passed, 3 skipped, 2 xfailed in 99.21s (0:01:39)
    ```

    THE FAILURE SETS ARE IDENTICAL, proven mechanically rather than by eye (both runs' `FAILED` lines captured, sorted, and diffed):

    ```
    $ diff baseline-failures.txt after-failures.txt && echo "IDENTICAL FAILURE SET: no new failure introduced"
    IDENTICAL FAILURE SET: no new failure introduced
    ```

    39 more tests pass and none newly fails. THE 31 BASELINE FAILURES ARE ENVIRONMENTAL AND PRE-EXISTING, and the cause was diagnosed rather than assumed: the driver exports `AW_EXECUTION_ROLE=worker` into the lane, and `agent_workflows/ipd_lifecycle.py:69` correctly refuses `begin`/`finalize` for a worker-role process with `AW-LIFECYCLE-ROLE-001`; 31 tests across five files call those verbs without neutralizing the variable. Clearing it turns the whole suite green, which proves both the cause and that the tree is clean:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest        # BEFORE my changes
    7676 passed, 3 skipped, 2 xfailed in 99.32s (0:01:39)

    $ env -u AW_EXECUTION_ROLE python3 -m pytest        # AFTER my changes
    7715 passed, 3 skipped, 2 xfailed in 102.82s (0:01:42)
    ```

    This is a real defect in test isolation (not a product defect, and the refusal itself must NOT be weakened) and is filed as backlog `770fkp`, because a red baseline in every lane invites an executor either to chase 31 phantom failures or to learn to wave failures away.

    BOTH HOSTS' SUITES GREEN BY NAME:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -o addopts="-q"
    251 passed in 39.34s
    ```

    (With the worker role left set, those two files show `17 failed, 234 passed`, all 17 members of the same environmental set.)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OPEN QUESTION GATE. OQ-03 is `Blocking: yes` and OPEN. `aw ipd lint` refuses this plan at every checkpoint
until the maintainer answers it, which is intended: THE SPLIT is not executable on this plan's own
authority. E-01 through E-05 are all authorized unconditionally, because E-04 delivers the ANALYSIS the
decision needs rather than performing the relocation. E-02's per-host flag contract is worth landing under
EVERY route, including "do not split", because no existing test states each host's own shipped flag set
(`test_run_flag_surface.py` checks the surface against the SPEC, not per host).

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`; do NOT add
`-n0`, a second `-q`, or `-p no:randomly`. The `Scope-Paths` fence is a DECLARATION so the runner can tell
afterwards whether an out-of-scope file was edited or an in-scope file was not: an out-of-scope edit is made
and then JUSTIFIED at finalize with a `--scope-reason`, and a declared-but-unmodified path needs a
`--scope-ack`. `tests/test_run_flag_surface.py` may legitimately end up either edited (if E-02's assertions
extend it) or acked (if they land in the new file); either is fine, but say which.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, REWRITTEN 2026-09-16. F-7's verification-dest collision, because it is the
one place in this Set where the maintainer's oc-preferred ruling would actively BREAK a shipped CLI and where
the losing host already carries a build-time guard proving it. F-6, because the Concern's "mostly drift"
sentence contradicts this plan's own F-1 and the measurement sides with F-1. F-3's economics, because twelve
of the seventeen shared flags are ALREADY registered from one place, which is what makes the split's payoff
small. NOTE FOR THE NEXT REVIEWER: F-9 and F-10 are GOOD news (zero pins, cleanest closure in the Set), so
this is the one split child where the obstacle is worth-it rather than can-it-be-done; do not spend the
budget looking for mechanical blockers.
