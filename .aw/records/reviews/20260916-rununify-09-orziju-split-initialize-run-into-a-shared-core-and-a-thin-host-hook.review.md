# Review findings: plan orziju

- Subject-Id: orziju
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `4602befb`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the eighth
`rununify` child reviewed and the FOURTH split child, and it is the most interesting of the four because
its headline number is not merely insufficient, it is actively misleading.

THE MEASUREMENT REPRODUCES EXACTLY. 409 oc lines and 339 agy; 241/236 code lines; EXACTLY 15 differing
lines under AST normalization with docstrings stripped; SequenceMatcher similarity 0.9345, the HIGHEST of
the five large functions. The host-token count is FOUR, not the plan's six.

AND THE FIFTEEN CONCEALS THE DIVERGENCE RATHER THAN FAILING TO REVEAL IT. Two of the fifteen are the
`state` dict and the `queue.append` dict, one line each only after normalization. Unpacked, the `options`
dict this function freezes carries 23 distinct keys: TEN shared, SEVEN oc-only (`opencode`, `variant`,
`agent`, `launch_profile`, `auto`, `validate`, `no_audit`, plus a conditional `verify_*` block) and SIX
agy-only (`agy_executable`, `effort`, `timeout`, `new_session`, `dangerously_skip_permissions`,
`no_verify`). So by CONTENT this is the LEAST shared of the five large functions while looking like the
most shared by line count, and a "hook supplying host specifics" would have to supply thirteen of
twenty-three keys, which is the function's entire output.

THE SHARPEST HAZARD IN THIS SET IS IN THIS FUNCTION AND THE PLAN NEVER MENTIONS IT. `initialize_run`
writes `state['driver'] = {'path': str(Path(__file__).resolve()), 'sha256': sha256_file(Path(__file__))}`
(`oc_runipd.py:3562-3563`, `agy_runipd.py:2345-2346`). `__file__` is evaluated in the DEFINING module, so a
core relocated to `runner_shared` writes `runner_shared.py` for BOTH hosts.
`run_analytics_sources.driver_generation` (`:198-207`) maps the BASENAME through `DRIVER_GENERATIONS`
(`:133-138`) and its own comment states "the basename is the ONLY discriminator that works";
`run_viewer.py:858-870` string-matches `oc_runipd`/`agy_runipd` to label a run OpenCode or Antigravity.
Both would return `unknown` for every run created after the split. I checked for a test over the runners'
driver path and found none, so the entire suite would stay green while run analytics permanently lost host
attribution. That is a silent, durable, data-level regression from a refactor advertised as behavior-neutral.

TWO OF THE PLAN'S OWN FINDINGS ARE WRONG, in opposite directions. F-2 nominates the frozen queue shape as
THE hazard; measured, both hosts write the IDENTICAL 12-key set and differ only in the ORDER of `kind` and
`order`, which JSON does not treat as significant, so the risk is LOW and the review budget should not go
there. F-5 says "agy writes a `kind` key into each queue entry; oc does not"; both write it, and what
actually differs is that agy DERIVES it through `_plan_kind` because `agy.PlanRecord` lacks the field
(verified live: `kind in oc: True`, `kind in agy: False`). That is F-4's finding, so F-5 is a duplicate
carrying an inverted claim. F-6's stated reason is also wrong (the two gate calls differ by a `host=`
argument, not by line wrapping) though its conclusion holds.

WHAT THE PLAN GOT RIGHT AND SHOULD BE CREDITED FOR. F-1 and F-4 are correct and well sourced: agy's
`_plan_kind` fallback exists solely because its record lacks `kind`, the helper is still at
`agy_runipd.py:1660`, and ordering this child after `sy7uwh` genuinely removes work. F-3 is the best finding
in the plan and I strengthened rather than corrected it: agy has ZERO `runner_profiles` references against
oc's 17, so `launch_profile` is not a key agy forgot but a capability agy lacks, which makes it an A / NOT-A
case under the maintainer's ruling rather than an oc-preferred one, and
`tests/test_runner_profiles_e2e.py` (34 tests, green) reads `state["options"]["launch_profile"]
["config_digest"]` directly.

ELEVEN PINS READ THIS FUNCTION'S SOURCE, across three files, and two are ORDERING pins that split the
source on the literal `run_dir = state_root` to prove a refusal precedes durable state
(`tests/test_run_flag_surface.py:745`, `:1340`), with a third of the same shape at
`tests/test_dirty_base_gate.py:191`. `test_run_flag_surface.py:1338` cites SPEC 2.5a by name for that rule.
183 tests pass across the three files today. None was fenced.

CLOSURE: 34 free module-level names, 16 resolving in `runner_shared`, 2 equal constants, 4 already single
objects, 2 oc-only with no agy counterpart, 8 still DEFINED TWICE, plus `__file__`. Of this function's eight
double-defined names, sibling `i3d6ml` as re-scoped lifts NONE, so the declared prerequisite chain does not
thin the injection list.

ONE NEGATIVE FINDING RECORDED TO SAVE A MEASUREMENT: this function calls `atomic_write_json` directly and
has ZERO `save_state` call sites, so the `test_no_call_site_was_rewritten` census that all three sibling
children trip does NOT apply here.

WHAT I FIXED AND WHAT I LEFT. I added the `options` key table and the closure table to the Goal; added
F-9's `__file__` hazard with both consumers and the line citations; corrected F-2, retracted F-5, fixed
F-6's reason; added gating E-01 (two measurements, `__file__` named as non-relocatable); rewrote E-02 to pin
the driver-identity contract FIRST because it has no test today; added E-03 as a pin inventory that must not
edit a test; converted the split into E-04, an analysis gated on OQ-03; rewrote E-05 with the inverse
assertions; made non-vacuity bidirectional with a control that proves the suite would catch F-9; fenced five
test files; and sharpened the spec section on the two spec-cited ordering pins. I did NOT decide the route.

MY RECOMMENDATION IS STRONGER HERE THAN FOR THE SIBLINGS, because the seam is unusually clean: the PREFIX
of this function (refusals, resolution, the three gates) is genuinely identical apart from a `host=` string
and is where the ordering pins live, while the SUFFIX (the state and options writer) is legitimately
host-owned. Sharing the prefix and leaving the suffix host-owned shares exactly what is shared, and the
boundary falls precisely where the existing pins already assert one.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | BLOCKER | IN-SCOPE | A. correctness (data integrity); C. architecture | `oc_runipd.py:3562-3563`; `agy_runipd.py:2345-2346`; `run_analytics_sources.py:198-207`, `:133-138`; `run_viewer.py:858-870` | **A RELOCATED CORE SILENTLY DESTROYS THE HOST-IDENTITY DISCRIMINATOR AND THE PLAN NEVER MENTIONS IT.** `initialize_run` writes `state['driver']['path']` from `__file__`, which is evaluated in the DEFINING module, so a shared core writes `runner_shared.py` for both hosts. `driver_generation` maps the BASENAME (its comment: "the basename is the ONLY discriminator that works") and `run_viewer` string-matches the module name. Both return `unknown` for every post-split run. NO test covers the runners' driver path, so the suite stays green while run analytics permanently loses host attribution. | C:Low; U:Low; S:Low; F:High; Overall:High | OPEN | Added as F-9 with both consumers; E-02 now pins the contract BEFORE any split and V-05(b) requires a control proving the suite would catch it; E-04(b) must state how `__file__` would be handled. Folded into OQ-03. NOT fixed by a plan edit because the handling choice is part of the route decision. |
| PR-002 | BLOCKER | IN-SCOPE | C. architecture; G. executability | `options` key measurement at HEAD `4602befb` | **THE FIFTEEN-LINE COUNT IS EXACT AND CONCEALS THE DIVERGENCE.** Two of the fifteen are dict literals; unpacked, `options` carries 23 keys of which 13 are host-specific (7 oc-only, 6 agy-only, 10 shared). So this is the LEAST shared of the five large functions by content while having the HIGHEST similarity (0.9345) by line. A shared writer would supply thirteen keys, which is not a hook but the function's whole output. Same inference error as siblings `i3d6ml`, `ty3cj6`, `yrqyxb`, except here the metric actively misleads. | C:High; U:Low; S:Low; F:Medium; Overall:High | OPEN | `options` table added to the Goal; F-7 promoted into F-8; gating E-01(a) measures the partition; E-04(a) must answer whether a 13-of-23 writer is worth sharing; escalated as OQ-03 with four routes and a share-the-prefix recommendation. |
| PR-003 | HIGH | IN-SCOPE | A. correctness (an inverted claim) | queue-entry key measurement; live `PlanRecord._fields` | **F-5 IS FACTUALLY WRONG AND IS A DUPLICATE OF F-4.** It states agy writes a `kind` key and oc does not; BOTH write it, and the twelve-key sets are equal. The real difference is that agy DERIVES the value via `_plan_kind` because `agy.PlanRecord` lacks the field. An executor acting on F-5 would look for a key oc does not write and find one, then either add a nonexistent difference to the resolution table or conclude the measurement was untrustworthy. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 RETRACTED in place with the measurement and redirected to F-4 (retained rather than deleted so the inverted claim stays visible as a correction). |
| PR-004 | HIGH | IN-SCOPE | A. correctness (a hazard mis-ranked) | queue-entry key sets; JSON ordering semantics | **F-2 NOMINATES A LOW RISK AS THE HAZARD, which misdirects the review and the validation budget.** Both hosts write the identical 12-key set and differ only in the position of `kind` and `order`, which JSON round-trips do not preserve as significant. Meanwhile the severe hazard (PR-001) is unnamed. A plan that tells its executor to spend the hazard budget on the queue shape will under-test the thing that actually breaks. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-2 downgraded in place with the measurement, the resume proof KEPT (cheap and correctly shaped, now Required tests item 4), and the reviewer-targets paragraph rewritten to point at F-9 instead. |
| PR-005 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | three test files; 11 pins; `183 passed`; spec 2.5a citation | **ELEVEN PINS READ `initialize_run`'s SOURCE AND A THIN CALLER SATISFIES NONE.** Eight in `test_run_flag_surface.py`, two in `test_dirty_base_gate.py`, one in `test_runner_backlog_close.py`. THREE are ordering pins encoding "a refusal precedes any durable state" (`:745` and `:1340` split on the literal `run_dir = state_root`; `test_dirty_base_gate.py:191` requires the dirt report between two other calls), and `:1338` cites SPEC 2.5a by name. `:1564` additionally requires EXACTLY ONE call site per gate. None was fenced. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | FIXED | All three fenced; F-10 enumerates all eleven with `path:line` and what each asserts; E-03 must produce a per-pin verdict plus a behavioral equivalent for the three ordering pins WITHOUT editing a test; V-03 requires the green baseline. |
| PR-006 | HIGH | UNDER-SCOPE | C. architecture (capability asymmetry) | zero `runner_profiles` refs in agy vs 17 in oc; `tests/test_runner_profiles_e2e.py` | **F-3 IS RIGHT AND UNDERSTATES ITS OWN CASE.** It warns against collapsing the launch half into the verification half; measured, there is no agy half at all. `launch_profile`/`resolve_launch_pair`/`launch_profile_record` are oc-only because agy has no profile store, so under the maintainer's ruling this is an A / NOT-A case needing a per-symbol decision, NOT an oc-preferred case. A shared writer emitting `launch_profile` for both hosts would fabricate provenance agy cannot supply; emitting it for neither breaks `test_runner_profiles_e2e.py`, which reads `config_digest` directly. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-11 with the counts; recorded in Project conventions; Required tests item 7 names the suite; E-04(d) must decide-or-escalate the treatment; folded into OQ-03. |
| PR-007 | MEDIUM | IN-SCOPE | A. correctness (a stated reason that is wrong) | AST-normalized diff | **F-6 ATTRIBUTES A REAL DIFFERENCE TO FORMATTING.** The two shared-gate calls differ by the `host='oc'` versus `host='agy'` ARGUMENT, which is a genuine host token and accounts for two of the four host-token lines, not by "wrapped-line formatting". The conclusion (no behavioral difference in the caller) survives; the reason does not, and a reader trusting it would not realize the gates are already host-parameterized. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 corrected in place, with the `test_run_flag_surface.py:1564` one-call-site constraint noted so a shared writer cannot change the count. |
| PR-008 | MEDIUM | IN-SCOPE | A. correctness (a count in the plan's favor) | host-token measurement | The Concern claims SIX host-token lines; measured FOUR. Small, and it errs in the direction that makes the divergence look more like drift, which is the same direction as PR-002, so it is corrected rather than absorbed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in the Concern with the measured figure. |
| PR-009 | MEDIUM | IN-SCOPE | C. architecture (a guard cited as evidence it is not) | `tests/test_review_findings_cascade.py:308-313`; 10 matches in agy | The plan cites `test_no_runner_to_runner_import` as forbidding a runner-to-runner import; it is a SUBSTRING check agy's `from agent_workflows.oc_runipd import (...)` form evades ten times, and TWO of this function's closure names (`announce_run_order`, `run_order_rationale`) are single objects precisely because agy imports them from oc. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in Project conventions, redirected to the AST-based `tests/test_runner_shared.py:955`. |
| PR-010 | MEDIUM | UNDER-SCOPE | G. right-sizing | E-02 as authored | One E-item bundled a 409-line relocation, thirteen `options` key decisions, an unnamed `__file__` hazard, eight injected dependencies and eleven pin repairs into one pass, which the count-based lint cannot see. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-13; restructured into five test-only items; `Highest E allocated` raised to 05. |
| PR-011 | MEDIUM | UNDER-SCOPE | E. non-vacuity | Required tests item 3 as authored | Non-vacuity was one-directional and, worse, pointed at the wrong hazard: sabotaging the shared core proves nothing about F-9, whose failure mode is a SUCCESSFUL split that writes the wrong driver path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 6 now demands both controls, the second specifically proving the suite would catch F-9 by accepting `runner_shared.py` and observing the failure; V-05(b) requires both pasted. |
| PR-012 | LOW | UNDER-SCOPE | G. spec effects | `tests/test_run_flag_surface.py:1338` citing spec 2.5a; `state['driver']` consumers | The spec section says "no spec change expected" without noticing that the ordering pins encode a SPEC-CITED rule and that `state['driver']` is consumed as the host discriminator, so both a pin conversion and a driver-path change are spec-governed rather than internal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec section rewritten to name both, requiring the amendment in the same change if either is touched; E-04 must surface them before a route is chosen. |
| PR-013 | LOW | IN-SCOPE | E. achievable bar | sibling `i3d6ml` flake; the gate paragraph | No baseline given for a known load-dependent flake, and the reviewer-targets paragraph aimed at F-2, which the measurement downgraded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 9 requires an own-HEAD baseline and reproduction before attribution; targets rewritten to F-9, F-8, F-11 with an explicit "do not spend the budget on F-2"; bare-run flags named; the pin-file `--scope-ack` expectation stated. |
| PR-014 | LOW | IN-SCOPE | D. anti-regression (a census correctly absent) | zero `save_state` sites in `initialize_run` | NOT A DEFECT, recorded so it is not re-measured: this function calls `atomic_write_json` directly and has ZERO `save_state` call sites, so the `test_no_call_site_was_rewritten` census that all three sibling split children trip does NOT apply here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-12 as an explicit negative finding. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | The plan reports 15 differing lines, the lowest in the Set. Accept that this is the easiest split, or unpack the lines? | UNPACK. Two of the fifteen are dict literals hiding 13 host-specific `options` keys, so this is the LEAST shared of the five by content. | (a) Accept the count and treat this as the cheap child, rejected because three sibling reviews had already shown line-difference to be the wrong unit, and a low count deserves MORE suspicion than a high one once that is known. (b) Unpack only the `state` dict, rejected: the `queue.append` dict needed the same treatment and it is what produced the F-5 correction. | AST-normalized diff at HEAD `4602befb`; the 23-key `options` partition (10/7/6); similarity 0.9345 | yes |
| D-2 | Should I look for hazards the plan did NOT name, given F-2 is stated as THE hazard? | YES, and it found the severe one: `__file__` relocation destroys the host discriminator. | (a) Verify only the stated hazard, rejected: the rubric requires checking the real production target, and a plan's own hazard list is exactly the kind of claim that can be complete-looking and wrong. (b) Note `__file__` as a closure entry and move on, rejected outright: it is not an injectable symbol, its MEANING changes on relocation, and the consumers make that a data-level regression rather than a build error. | `oc_runipd.py:3562`; `run_analytics_sources.py:198-207` and its "basename is the ONLY discriminator" comment; `run_viewer.py:858-870`; no test found over the runners' driver path | yes |
| D-3 | F-2 says the queue shape is the hazard and F-5 says agy writes a key oc does not. Trust or measure? | MEASURE. F-2 is LOW risk (identical 12-key sets, only `kind`/`order` position differs) and F-5 is inverted (both write `kind`). | (a) Trust both, rejected: they are the two findings that direct the executor's validation effort, so an error in either misallocates the whole proof budget. (b) Correct F-5 by deleting it, rejected: a retracted finding left visible with its correction tells the next reader the claim was tested, where a deletion invites its rediscovery. | queue-entry key extraction from both hosts; live `PlanRecord._fields` showing `kind` present in oc and absent in agy | yes |
| D-4 | Eighteen-key writer, `__file__`, eleven pins. Choose a route myself, or ask? | ASK. Raised as OQ-03, `Blocking: yes`, four routes with costs and a share-the-prefix recommendation. | (a) Adopt share-the-prefix myself, rejected: it redefines the child's scope from "split the function" to "share its first half", which changes what the Set delivers and is the maintainer's call. (b) Share everything with thirteen key parameters, rejected: it contradicts the `818uru` OQ-02 wrapper ruling and produces a template whose output is entirely caller-supplied. (c) Declare the function host-owned myself, rejected for the same authority reason, though it is defensible. | the `818uru` OQ-02 ruling quoted at `tests/test_runner_shared.py:64-70`; the 13-of-23 measurement; F-9; the two ordering pins marking a natural boundary | yes |
| D-5 | Should E-02 pin the driver-identity contract even though no split may ever happen? | YES, unconditionally, under every route including "do not split". | (a) Gate the test behind OQ-03 with the split, rejected: the contract is UNTESTED TODAY, so the test has standalone value and is the only artifact of this plan that improves the repository regardless of the route chosen. (b) File it as a separate backlog item, rejected: this plan already owns the function on both hosts, and deferring a test whose absence is what makes F-9 silent would leave the hazard undetectable for the next agent too. | `run_analytics_sources.driver_generation` and `run_viewer`'s label logic having no runner-side test; F-9's silence being caused precisely by that absence | yes |

### Deferred and open

- `PR-001` - `OPEN`:
  - Reason: How `__file__` is handled is inseparable from the route decision. Passing the caller's module path into a shared core is the only correct answer, but whether a shared core should exist at all here is exactly what OQ-03 asks, and the handling cannot be specified before that.
  - Remediation Risk: High
  - Axis: functionality
  - Required decision or evidence: the maintainer's answer to OQ-03; if a split is authorized, an explicit decision that the caller's module path is threaded through and proven by E-02's test.
  - Consequence if unresolved: none today, and E-02's test lands under every route so the hazard becomes DETECTABLE regardless. The risk being held open is a future executor performing the relocation without that test, after which every run reports `unknown` for its host generation, silently and durably, with the whole suite green.
- `PR-002` - `OPEN`:
  - Reason: Thirteen of twenty-three `options` keys are host-specific and one reflects a capability agy does not have, so whether this function should be shared is a design question rather than a sequencing one, and every route restructures a Set with nine pending children.
  - Remediation Risk: High
  - Axis: complexity, functionality
  - Required decision or evidence: the maintainer's answer to OQ-03, choosing among routes A through D.
  - Consequence if unresolved: `initialize_run` stays duplicated. That cost is genuinely LOW here compared with the other split children, because the duplicated part (each host's own option set and launch identity) is the part that is legitimately host-specific, and the shared part (the gate sequence) is already reached through shared functions. The dangerous outcome is an executor following the plan as written and producing a thirteen-parameter writer.

### Escalation of the irreversible decision

None of this round's decisions is judged `Reversible: no`. Each of D-1 through D-5 is undone by editing this
plan or deleting a test, and none publishes an interface, migrates data, or deletes anything. Stated
explicitly rather than left blank, because the three sibling reviews each carried one irreversible decision
and a reader comparing them should see that the difference is deliberate: in those plans I DECLINED to
authorize rewriting an existing pin, which is irreversible in the direction of the alternative. Here the
pin question is identical in shape but the decision is deferred WHOLE to OQ-03 rather than partly resolved,
so no irreversible act is being licensed by me. The `Blocking: yes` OQ-03 is what puts the pin-conversion
question in front of the maintainer, and E-03 pre-writes the behavioral equivalents so the decision is
cheap when it comes.

### Honest limits of this review

- I DID NOT ATTEMPT THE SPLIT. The 13-of-23 and eight-injection figures come from static AST analysis plus
  live `is` and `_fields` inspection, not from having built a shared writer. E-01 re-derives both at
  execution HEAD.
- MY F-9 CLAIM IS MECHANISM PLUS CONSUMER READING, NOT AN OBSERVED FAILURE. I established that `__file__`
  resolves in the defining module, that both runners write it into `state['driver']['path']`, and that two
  consumers discriminate on its basename. I did NOT relocate the function and observe `driver_generation`
  returning `unknown`. E-02's test is written to be that proof, and V-05(b)'s control is what demonstrates
  the test would catch it.
- I SEARCHED FOR A DRIVER-PATH TEST AND FOUND NONE, by grepping `tests/` for `driver_generation`,
  `DRIVER_GENERATIONS` and `state['driver']` spellings. A test reaching the field dynamically, or asserting
  it through a fixture I did not recognize, would not have appeared. "No test covers this" is therefore a
  strong claim resting on a keyword search.
- I DID NOT RUN THE FULL SUITE. I ran the three pin files (`183 passed`) and
  `tests/test_runner_profiles_e2e.py` (`34 passed`). The plan's overall suite bar is unverified by me, and
  the flake I warn about is inherited from a sibling review's measurement.
- MY `options` PARTITION IS SYNTACTIC. I classified keys by presence in each host's dict literal; I did not
  verify that each shared key means the same thing at runtime on both hosts, and `no_audit` versus
  `no_verify` is a reminder that two hosts can spell one concept differently and be counted as
  host-specific by a key-name comparison.
- I DID NOT DECIDE THE ROUTE (D-4), and my share-the-prefix recommendation is a recommendation. I also did
  not evaluate whether `initialize_run` SHOULD share its prefix given that the prefix is already composed
  of calls into `runner_shared`, which would make route (B)'s benefit smaller than it appears; E-04 should
  test that premise rather than inherit it from me.

## Round 2

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round records that round 1's gating findings were
resolved by the maintainer's own directive, given on 2026-09-16 in an interactive session. Nothing in the
plan was re-reviewed here and no new finding was sought; appending a round is the mechanism
`plan-review.md` prescribes for this, since the gate reads only the current round. Round 1 is left exactly
as written, and its measurements remain the specification the execution must reproduce at execution HEAD.

THE DIRECTIVE, quoted: "at the end of the SET, there should be one code base shared by the two runners
that contains 100% of the otherwise redundant code that currently is duplicated between the two runners."

TWO SUPPORTING RULINGS the maintainer gave in the same session, because round 1's findings rested on
premises both of them contradict. FIRST, TESTS ARE NOT IMMOVABLE: asked directly whether the
source-reading guards prevent this work, the answer was no, and the maintainer pointed at this
repository's own precedent where such a guard was already re-based for shared code
(`tests/test_nested_tty_noninteractive.py:190-203`, whose docstring records the reasoning; all 41 tests in
that file and `tests/test_lane_tool_identity.py` pass at this HEAD, verified 2026-09-16). SECOND,
COORDINATED DE-DUPLICATION IS PERMITTED: many functions may be de-duplicated together before testing, so
a dependency that is still double-defined because a sibling has not landed is an ordering matter, not a
blocker. What remains forbidden is weakening a guard silently.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Body difference was measured but liftability was not: the function closes over names that are still defined twice, so a shared core would need many injected parameters. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled 2026-09-16 that the objective is 100% de-duplication and that the injected-parameter form IS the sanctioned mechanism, not a violation of it: the 2026-09-03 `818uru` OQ-02 ruling established "shared file owns the real function taking explicit parameters, each runner keeps a one-line wrapper at the original name and signature", and what it rejected was threading a parameter through ~86 CALL SITES, which the wrapper form avoids. The maintainer also confirmed many functions may be de-duplicated together before testing, so a still-double-defined dependency is handled by working in dependency order, not by refusing. See the resolved OQ-03. |
| PR-002 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Tests read this function's source text or patch names it resolves, and a thin caller satisfies none of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled 2026-09-16 that these pins are work, not vetoes, citing the existing precedent where such a guard was already re-based onto shared code successfully (`tests/test_nested_tty_noninteractive.py:190-203`, all 41 related tests passing at this HEAD). A pin is to be re-based on the new location with its property preserved and its injected-regression proof kept; silently weakening one (lowering a threshold, deleting an assertion) remains forbidden. Where a behavioral assertion can replace a source-text one without losing coverage, prefer it and say so. See the resolved OQ-03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's directive discharge round 1's gating findings, or do they need a fresh review pass? | It discharges them; record the discharge and leave round 1 untouched. | A further full review round on this plan, rejected on cost and on relevance: round 1 already measured the mechanics correctly and its findings were escalations of a SCOPE decision, which is the maintainer's to make and which they have now made. | The findings' own recorded remedy was a maintainer decision, and that decision is now recorded in this plan's resolved OQ-03 with its reasoning and its two supporting rulings. | yes |

HONEST LIMIT, stated because it bounds what this round proves: the discharge rests on the maintainer's
directive, NOT on an independent reviewer's re-examination of the plan's content. Round 1 is where that
assurance lives. Specifically NOT re-verified here: the closure and pin measurements round 1 recorded
(each plan's E-01 re-measures them at execution HEAD and is required to refuse on a stale list), and
whether the re-based guards preserve their properties (each plan's V-items require that evidence). This
round changes the DECISION column and nothing else.
