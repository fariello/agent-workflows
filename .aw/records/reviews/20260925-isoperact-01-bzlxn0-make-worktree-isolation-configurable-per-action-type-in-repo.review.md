# Review: Make worktree isolation configurable per action type in repository policy

- Subject-Id: bzlxn0
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a1b2d11a`, in the review sweep lane. The target plan was committed and unchanged (the
lane's rev-3 materialized copy is byte-identical to the tracked file), so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported `clean`
(exit 0) before review and `--phase review-finalize --agent` reports `clean` with zero findings after every
edit below, including the E/V renumbering to E-01..E-08 / V-01..V-08.

THE PLAN'S SURVEY OF WHAT EXISTS IS ACCURATE AND ITS DESIGN FOLLOWS A REAL PRECEDENT. F-1 and F-2 both hold:
isolation is one boolean, `config.py` contains no isolation key, and the single flag genuinely governs two
action types. The `read_run_policy` / `policy_retry_budget` pattern it copies is the right one, including the
warn-and-fall-back posture, whose recorded reason I confirmed in that section's own comment ("a per-invocation
mistake refuses; a shared-file mistake warns and continues"), and the claim that such keys are deliberately
absent from the config schema checks out (`CONFIG_SCHEMA` has 11 keys and no `run.*` member beyond
`defaults.prune`). F-3's argument for leaving orchestrator retirement alone is sound.

THE FINDING THAT CHANGES THE PLAN IS PR-201: `review: false` WOULD DISCARD THE REVIEW'S OUTPUT. I traced the
review path rather than the policy path, and the whole output mechanism is gated on the lane handle. The only
writer of `wt_handle` on a review turn is `if is_review and isolate:`; the output block is
`if is_review and wt_handle is not None:`, which calls `commit_review_lane_output` and then
`integrate_review_lane_branch`. So with review isolation off, no lane is allocated, `wt_handle` stays `None`,
and the review's two outputs (the plan edit and the review record) are left UNCOMMITTED in the shared
checkout. There is no third path: those two functions are the only route a review's files take to the
repository.

THAT IS NOT A NEW HAZARD, IT IS A CLOSED ONE, WHICH IS WHAT MAKES IT SERIOUS. Executed plan `ajxr5d` removed
exactly this state after measuring it live: "reviewing the orchestrator `8lfoum` produced commit `59cdc718`
holding five files, three of them sibling child plans ... still `queued` in the same run ... uncommitted for
the turn's duration (~36 minutes) ... a concurrent `runanalytics` execute run had its items refused against
them. This is not a theoretical concurrency risk; it happened while the maintainer watched." That plan's own
execution record goes further and names the failure mode this policy would re-create: "FAIL-CLOSED: a review
whose lane allocation fails is marked `blocked` and never falls back to the shared checkout, because that
fallback is the behavior this plan removes and would be invisible." I verified the fail-closed guard is real
(an allocation exception sets `fail-lane` and returns without launching) and, crucially, that a POLICY switch
BYPASSES it rather than tripping it: a false `isolate` never enters that `try` at all. So the loss would be
silent. Two items now close this: E-05 requires the output to land in the shared checkout or the policy value
to be refused, and E-06 requires a run-start warning. I also raised OQ-02, because whether the option should
exist at all is a risk-appetite judgement that belongs to the maintainer, not to me.

I ALSO CHECKED WHETHER A SPEC FORBIDS IT, and the answer is a useful asymmetry rather than a clean no. Spec
`7ckptx` R5.4 keeps a NORMATIVE refusal in force for a shared-tree turn with dirty tracked paths, and its only
live caller is `evaluate_clean_base_for_launch(repo, shared_tree=not isolate)` guarded by
`if self_finalize and not is_review:`. So `execute: false` lands inside an existing, spec-backed refusal, while
`review: false` sits outside it entirely. The "reviews were exempt" phrase in R5.4's 2026-09-16 amendment note
is a measured cost observation about how many items that gate blocked, not a normative carve-out, so it cannot
be cited as permission. That asymmetry is now stated in the gate, because it is the reason the two halves of
this feature deserve different levels of caution and should not be approved as one undifferentiated change.

PR-202 IS THE ERROR AN EXECUTOR WOULD HIT IMMEDIATELY. E-03 prescribes `if args.isolate_worktree is False`.
Because `isolate_worktree` is NOT a member of `RUN_POLICY_FLAGS` (I listed the table: 16 flags, none of them
this one), a namespace built generically over that table leaves the attribute ABSENT, so that expression
raises `AttributeError` rather than evaluating false. There are four states, not two: `False` (typed flag),
`None` (E-02's new default), ABSENT (`resume`, and generic test namespaces), and `True` (what every existing
fixture namespace passes explicitly, in at least three test modules). The `True` case is the one with a real
decision in it, and the plan never mentions it: read as an override it lets existing fixtures silently defeat a
repository policy, read as "not supplied" the flag cannot force isolation on against a policy. I recorded the
recommendation (defer to policy, following `freeze_run_policy_flags._supplied`'s documented rule that a
placeholder bool "can only mean ... ABSENT") and required the implemented meaning to be stated and tested.

PR-203: E-04 UNDERSTATES ITS OWN EDIT. It says "route the two launch-site reads", but the second one is an
ASSIGNMENT feeding FOUR reads: `shared_tree=not isolate`, two `if isolate:` reads inside
`if self_finalize and not is_review:`, and `if is_review and isolate:`. Substituting the assignment is in fact
safe today, because the three non-sweep reads are reachable only when `not is_review` - but that safety rests
on guards the plan does not state, so an executor cannot verify it, and a future edit removing a
`not is_review` guard would silently hand an execute-only site the review value. V-04 now requires the four
reads and their enclosing guards to be pasted.

PR-204 IS A VALIDATION THAT CANNOT FAIL. V-01 required `grep -c isolate agent_workflows/project_schema.py`
to be "unchanged from before". That module governs placements, presets and physical config; it contains no
`run.*` key and nothing this plan touches, so the count is zero before and after no matter what E-01 does. The
schema the key is deliberately absent from is `config.CONFIG_SCHEMA`, so the assertion now targets that.

PR-205 records what I verified rather than assumed about the audit flag, because the plan's caution there was
correct and deserved to be a measurement: `start` and `audit` are separate subparsers with separate namespaces
that happen to share the `isolate_worktree` dest. Parsing both proves independence (`start <id6>` -> `True`,
`start --no-isolate-worktree` -> `False`, `audit <id6>` -> `True`, `audit --no-isolate-worktree` -> `False`,
the last because `BooleanOptionalAction` generates the `--no-` form itself), and `resume` leaves the attribute
absent. I also found a third `args`-level read the plan's audit instruction does not name,
`oc_runipd.audit`'s own `getattr(args, "isolate_worktree", True)`, which must keep its `True` default.

PR-206 strengthens a deferral that was right for a weaker reason. The plan declined a per-action CLI flag
because it "widens the frozen `RUN_POLICY_FLAGS` contract for no demonstrated need". The real constraint is
harder: that table is CLOSED and asserted against spec `25kzda` 2.1, and `register_display_flags`'s own
docstring records that registering a non-spec flag there fails the surface contract. So a new flag would need a
spec amendment this plan does not declare. Same conclusion, but now an executor cannot talk themselves out of
it. (Note the contract test that enforced this, `tests/test_run_flag_surface.py`, was deleted in `19313eed`'s
suite trim; the docstring constraint stands and the spec does too, but the mechanical guard does not currently
run, which is worth knowing before relying on it.)

PR-207 resolves OQ-01 rather than leaving it for the maintainer, because the repository answers it. Its own
default was already yes; what makes it decidable without asking is F-8's measurement that a policy disabling
isolation bypasses the fail-closed guard, so nothing else in the run would report it, combined with
`config.py`'s recorded principle for precisely this situation ("a silent fallback would override a repository
that believes it set a policy with no signal anywhere"). It is built as E-06, scoped to emit nothing when both
actions are isolated so a default run's output is byte-identical.

Backlog `h2mpru` carries no `- Blocks-Release:`, so no gate is inherited and the gate section says so. Its
motivation (disk is linear in parallelism) is real but narrow against this repository's measured 46M and 0.31s,
which is why `low` priority is right and why OQ-02's conservative default costs little: execute lanes are the
parallel ones, so per-action control over `execute` alone already serves the disk argument.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression (a configuration value that silently discards work) | `if is_review and isolate:` is the sole writer of `wt_handle` on a review turn; the output block is `if is_review and wt_handle is not None:` -> `commit_review_lane_output(...)` then `integrate_review_lane_branch(...)`; the sweep-lane `except Exception` sets `fail-lane` and returns, so a false `isolate` bypasses that guard instead of tripping it; `ajxr5d` Concern (commit `59cdc718`, five files, three sibling child plans still `queued`, ~36 minutes uncommitted, a concurrent run's items refused) and its E-02 record ("never falls back to the shared checkout, because that fallback is the behavior this plan removes and would be invisible") | `review: false` DISCARDS THE REVIEW'S OUTPUT AND DOES IT SILENTLY. With no lane there is no handle, so the only path a review's plan edit and review record take to the repository is skipped entirely and both are left uncommitted in the shared checkout. That is precisely the state executed plan `ajxr5d` removed after measuring it live, and it is reached by BYPASSING the fail-closed guard that plan installed, so nothing reports it. No item addressed this: the plan treats disabling review isolation as purely a cost saving. | C:Medium (a second output route, or a refusal, must be written); U:Low; S:Low; F:Medium-High (silent loss of review output and a dirty shared tree mid-run); Overall:Medium | FIXED | E-05 added: land a non-isolated review's two files with a path-scoped commit reusing `commit_review_lane_output`'s discipline, OR have E-01 refuse `review: false` with a warning, recording which route was taken. E-06 added for run-start visibility. F-6/F-7/F-8 added with the measurements. Scope check rewritten. OQ-02 raised (non-blocking, `- Finding: F-6`) so the maintainer decides whether the option should exist. V-05 requires a negative control. |
| PR-202 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability (a prescribed expression that raises) | `[row.flag for row in RUN_POLICY_FLAGS]` -> 16 flags, none `--no-isolate-worktree`; `hasattr(Namespace(**{row.dest: False for row in RUN_POLICY_FLAGS}), "isolate_worktree")` -> False; `resume <run>` leaves the attribute ABSENT; `isolate_worktree=True` passed explicitly by fixtures in `tests/test_hostdedup_third_host.py`, `tests/test_runner_active_conflict.py`, `tests/test_orchestrator_retirement.py`; `freeze_run_policy_flags._supplied`'s rule that a placeholder bool "can only mean ... ABSENT" | E-03'S PRECEDENCE TEST RAISES ON A NAMESPACE THE CODEBASE ACTUALLY BUILDS, AND IGNORES TWO OF FOUR STATES. `args.isolate_worktree is False` raises `AttributeError` whenever the attribute is absent, which is the `resume` case and the generic-namespace case. The four real states are `False`, `None`, ABSENT and `True`, and the plan names one. `True` carries a genuine decision it never makes: as an override it lets existing fixtures silently defeat repository policy; as "not supplied" the flag cannot force isolation on. | C:Low; U:Low; S:Low; F:Medium (policy silently defeated, or an AttributeError on resume); Overall:Low | FIXED | E-03 now requires `getattr(args, "isolate_worktree", None)`, enumerates all four states, recommends "defer to policy" for `True` citing `_supplied`'s rule, notes no CLI form currently produces an explicit `True`, and forbids adding the key to `RUN_POLICY_FLAGS`. E-07(b) tests all four and requires the implemented meaning stated; V-03 requires a case for each. F-10 added. |
| PR-203 | MEDIUM | IN-SCOPE | A. Correctness (an understated edit surface) | In the launch function: `isolate = state.get("options", {}).get("isolate_worktree", True)`, then `evaluate_clean_base_for_launch(repo, shared_tree=not isolate)` and two `if isolate:` reads, all three inside `if self_finalize and not is_review:`, plus `if is_review and isolate:` | E-04 SAYS "THE TWO LAUNCH-SITE READS" BUT THE SECOND IS AN ASSIGNMENT FEEDING FOUR READS. The substitution is safe today because the three non-sweep reads are reachable only when `not is_review`, but the plan never states those guards, so an executor cannot check the claim, and a later edit removing a `not is_review` guard would silently feed an execute-only site the review policy value. | C:Low; U:Low; S:Low; F:Medium (an execute turn taking a review policy value); Overall:Low | FIXED | E-04 enumerates all four reads, names each enclosing guard, and instructs that the guards be READ rather than assumed; V-04 requires them pasted with annotations; F-5 added; the gate carries it as a stop condition. |
| PR-204 | MEDIUM | IN-SCOPE | E. Testing (an assertion that passes regardless) | `grep -n isolat agent_workflows/project_schema.py` -> nothing; that module's symbols are placements/presets/physical-config helpers with no `run.*` key; the relevant registry is `config.CONFIG_SCHEMA`, whose 11 keys exclude `retry_budget`, `on_conflict` and `review_findings_gate` | V-01 ASSERTS AGAINST AN UNRELATED MODULE. "`grep -c isolate agent_workflows/project_schema.py` unchanged from before" is zero before and after whatever E-01 does, because that file has nothing to do with the `run` policy object. The property actually worth pinning (the key stays out of the validated schema, per the `review_findings_gate` precedent) goes unchecked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now asserts `[k for k in config.CONFIG_SCHEMA if 'isolat' in k] == []`, adds the malformed-value warning case, and states why the authored grep proved nothing; E-01 records the verified precedent including the schema census. |
| PR-205 | LOW | IN-SCOPE | G. Plan executability (a correct caution left as an assumption, plus an unnamed third read) | Parsed both subparsers: `start abc123` -> `True`, `start abc123 --no-isolate-worktree` -> `False`, `audit abc123` -> `True`, `audit abc123 --no-isolate-worktree` -> `False`, `resume run-x` -> attribute ABSENT; `oc_runipd.audit` contains its own `if getattr(args, "isolate_worktree", True):` | THE AUDIT-FLAG CAUTION IS RIGHT BUT UNPROVEN, AND ONE READ IS UNNAMED. E-02 warns not to touch the audit parser without establishing that the shared dest name is harmless, which it is (separate subparsers, separate namespaces). Separately, E-02's instruction to "audit every `getattr(args, "isolate_worktree", True)` read on the RUN namespace" does not name `oc_runipd.audit`'s own read, which is on the AUDIT namespace and must keep its `True` default. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 carries the four parsed namespaces as a measurement, notes `resume` leaves it absent (which is why E-03 must treat absent and `None` alike), and names the `oc_runipd.audit` read as explicitly out of bounds; V-02 requires the namespaces pasted; a conventions bullet and a Deferred entry record the audit flag. |
| PR-206 | LOW | IN-SCOPE | C. Architecture (a deferral resting on the weaker of two reasons) | `register_display_flags`' docstring: "DELIBERATELY NOT IN `RUN_POLICY_FLAGS`: that table is the closed flag list spec `25kzda` 2.1 declares and `tests/test_run_flag_surface.py` asserts against the spec file"; that test file was deleted in `19313eed` | THE CLI-FLAG DEFERRAL IS RIGHT FOR A WEAKER REASON THAN THE REAL ONE. "No demonstrated need" is an argument someone can overturn by demonstrating a need; the actual constraint is that `RUN_POLICY_FLAGS` is CLOSED and spec-asserted, so a new flag needs a spec amendment this plan does not declare. Worth stating precisely because the mechanical guard no longer runs (its contract test was deleted in the suite trim), leaving the docstring and the spec as the only guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Deferred entry now cites the closed-table contract and the spec; E-03 forbids adding the key to the table; a conventions bullet records both the constraint and that its contract test is currently absent. |
| PR-207 | LOW | UNDER-SCOPE | F. UX / prevent silent failure (an open question the repository answers) | `config.py` run-policy section: "a silent fallback would override a repository that believes it set a policy with no signal anywhere"; F-8's measurement that a policy-disabled isolation bypasses the `fail-lane` guard so nothing else reports it; OQ-01's own stated default | OQ-01 WAS LEFT OPEN FOR THE MAINTAINER THOUGH THE REPOSITORY ALREADY DECIDES IT, and it covered only `execute`. A committed policy that turns off a safety property with no run-start signal is exactly the silent override this repository's own config section argues against, and PR-201 shows the review action needs the same visibility more than execute does. Asking spends a maintainer turn on a settled question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved as yes for BOTH actions with the cited basis, and built as E-06 (one line naming the key and disabled action(s); nothing when both are isolated, so a default run is byte-identical). V-06 requires all three cases including the silent default. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `review: false` discards the review's output (PR-201). Reject the plan, fix it in place, or ask the maintainer? | Fix it in place with E-05 (land the output, or refuse the value) AND raise OQ-02 for the maintainer on whether the option should exist. | (a) REPLAN / reject - rejected: the defect is one missing output route in an otherwise sound and well-precedented design, which is a bounded edit, not an unsound approach. (b) Fix silently and say nothing - rejected: whether to re-admit a review turn to the shared checkout is a risk-appetite call the maintainer owns, since E-05 closes the lost-output half but not the dirty-tree half. (c) Ask and stop without fixing - rejected: E-05 makes the value safe under EITHER answer, so execution need not wait on the judgement. | the lane-handle gate on the review output block; `ajxr5d`'s measured incident and its fail-closed note; the bypass-not-trip measurement | yes |
| D-2 | Should I resolve OQ-01 (warn on a policy that disables isolation) or leave it for the maintainer? | Resolve it as yes for BOTH actions and build it as E-06. | (a) Leave it open as authored - rejected: the repository answers it (config.py's own recorded principle against silent policy overrides) and the rule is not to ask what the repository answers. (b) Warn for `execute` only, as the question was scoped - rejected: PR-201 shows the review action has LESS surrounding protection, since R5.4's refusal does not reach it, so it needs the signal more. | `config.py`'s "no signal anywhere" reasoning; F-8's bypass measurement; OQ-01's own default | yes |
| D-3 | `True` on `args.isolate_worktree` is ambiguous and existing fixtures pass it. Treat it as an override or as not-supplied? | Recommend "defer to policy" and REQUIRE the implemented meaning to be stated and tested. | (a) Treat `True` as an explicit override - rejected: at least three existing test modules pass it, so policy would be silently defeated wherever those fixtures are reused. (b) Decide it myself and hard-code it - rejected: it is a precedence semantics choice with a live test surface, so the plan must state it and pin it rather than inherit it by accident. | `freeze_run_policy_flags._supplied`'s recorded rule that a placeholder bool means ABSENT; the three fixture call sites; no CLI form producing an explicit `True` | yes |
| D-4 | Does a spec forbid a non-isolated review, making this feature illegal rather than merely risky? | No: R5.4's refusal does not reach a review turn, so record the asymmetry instead of claiming a prohibition. | (a) Claim R5.4 forbids it - rejected: its only caller is guarded by `not is_review`, so asserting a prohibition would be false and would overstate the finding. (b) Cite the "reviews were exempt" note as permission - rejected in the other direction: that phrase is a measured cost observation inside an amendment note, not a normative carve-out. (c) Amend R5.4 to cover a non-isolated review - rejected as out of scope: no `.spec.md` is declared in Scope-Paths and it is a separate contract decision. | R5.4's SHARED TREE clause; `evaluate_clean_base_for_launch`'s `not is_review` guard; the 2026-09-16 amendment note's context | yes |
| D-5 | V-01 asserts against `project_schema.py`, which is unrelated. Correct it quietly or record it? | Record it as a finding and retarget the assertion to `config.CONFIG_SCHEMA`. | (a) Fix quietly - rejected: the failure mode is a validation that passes regardless of what was built, which is the class of error most worth naming so it is not re-introduced. (b) Drop the assertion - rejected: the property is real and matches the `review_findings_gate` precedent the plan cites, so it should be pinned, just against the right registry. | `project_schema.py` containing no `run.*` key; `CONFIG_SCHEMA`'s 11 keys excluding `retry_budget`/`on_conflict`/`review_findings_gate` | yes |
