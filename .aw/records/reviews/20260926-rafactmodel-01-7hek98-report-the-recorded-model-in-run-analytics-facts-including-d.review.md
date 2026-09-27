# Review: Report the recorded model in run-analytics facts, including display-name models and the verify phase

- Subject-Id: 7hek98
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e762c9c5` (the plan was authored at `61ef21d8`, an ancestor). The target plan was
committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and
`--phase review-finalize` reported `conforming` again after the edits. `aw check plans --agent`
reports 1 finding tree-wide and NONE against this plan, and `check_engine.evaluate_durable_carrier`
returns `[]`.

THIS IS A WELL-DIAGNOSED PLAN AND I RE-DROVE EVERY CODE CLAIM RATHER THAN READING IT. All four
functional findings hold exactly as written: `_model_of({"options": {"model": "Gemini 3.8 Flash
(High)"}})` returns `''` (the display name fails `_LABEL_RE` and is not path-shaped, so `_label`
drops it); `project_metric_facts({"model": "Gemini 3.8 Flash (High)"})` raises `PrivacyRefusal: key
'model' is not a short closed-vocabulary label`, independently of `_label`, which is the plan's
sharpest insight and the reason a one-surface fix would have failed; `_model_of` has no
`cost_attribution` fallback; and the PHASE loop passes one `model` to both the EXECUTE and VERIFY
entries. The producer contract is accurate too: `oc_runipd` writes both `COST_ATTRIBUTION_KEY` and
`"verify_" + COST_ATTRIBUTION_KEY` (the latter conditional on a resolved verifier), and `agy_runipd`
writes `cost_attribution.model = effective_model`, the same value as `options.model`, with
`resolve_card=False`. F-5's embedded-path hazard is real: `_looks_like_path("x /srv/y")` is `False`.

I ALSO PROTOTYPED THE PROPOSED FIX, which is the strongest thing I can say for it. The literal
`_MODEL_LABEL_RE` from E-04 plus the three guards admits `Gemini 3.8 Flash (High)`,
`provider/model` and a real profile id, and refuses every one of E-05 case (5)'s inputs plus a
Windows drive path and a double space. Driven through a patched `_project_scalar`,
`project_metric_facts({"model": "Gemini 3.8 Flash (High)"})` returned the value unchanged while
`{"outcome": "has spaces"}` still raised. So the mechanism works as specified, which is what a
review of a privacy-widening plan most needs to establish before arguing about anything else.

THE FINDING MOST LIKELY TO HAVE COST THE EXECUTOR THE WHOLE ITEM IS PR-1001, AND IT IS ABOUT WHERE
THE PLAN RUNS. E-01's survey globs `.aw/records/runs/*/state.json`. `records/runs/` is GITIGNORED
(`.aw/.gitignore`), and an execute turn runs in an ISOLATED LANE WORKTREE by default, so a lane has
no runs tree at all. Measured from THIS review's own lane: `.aw/records/runs` does not exist,
`run_viewer.discover_run_dirs(Path("."))` returns 0, and
`discover_run_dirs(runner_shared.runs_repo_root(Path(".")))` returns 283. The failure mode is worse
than a blocked item, because "0 runs found" is indistinguishable from "the defect is absent": an
executor could have reported the whole premise unreproducible and skipped the fix. The repository
already knows this trap and ships the resolver for it, and says so twice in `runner_shared` (the
`runs_repo_root` docstring records 0 versus 246 from lane `vddpml`; the `_SESSION_ID_KEYS` census
notes "this lane has no `.aw/records/runs` corpus"). E-01 now mandates the resolver, requires the
resolved root and run count as evidence, forbids reading zero as absence, and tells the executor to
proceed on the corpus-independent parts rather than stalling.

THE SECOND FINDING IS A SELF-DEFEATING INSTRUCTION, PR-1002. E-02 said to import
`runner_shared.COST_ATTRIBUTION_KEY`, "lazily inside the function if a module-level import would add
`runner_shared` to the import graph", and to verify with a `sys.modules` check "before and after,
keeping the answer unchanged". That cannot be satisfied: a lazy import still enters `sys.modules` the
first time `_model_of` runs, so the answer becomes call-order dependent and the check is either
trivially true (never called) or false (called once). The concern behind it is legitimate and I
measured it: `import agent_workflows.run_analytics` leaves `runner_shared` absent today,
`runner_shared.py` is 32452 lines against `run_analytics.py`'s 888, and adding it costs about 48ms
(118ms -> 166ms, min of 3 runs). So the resolution is the one the repository already uses for
cross-module string contracts: define the key locally with a comment naming the contract, and pin the
agreement with one assertion in the test, where importing the runner is free. That keeps the analytics
import graph clean AND makes drift a test failure rather than a hope.

THE THIRD IS A LATENT MIS-BINDING, PR-1003. The PHASE loop's first entry is not unconditionally
`Phase.EXECUTE`: its expression is `Phase.EXECUTE if item_phase is Phase.EXECUTE else item_phase`,
and `_phase_of` returns `Phase.REVIEW` for a `review` action. An executor implementing "pass the
verifier model for the VERIFY entry" with a conditional on the loop variable could plausibly write
something that also catches `Phase.REVIEW`. E-03 now says to bind the second entry (whose phase is
the literal `Phase.VERIFY`) or to carry the model in the loop tuple, and V-03 requires a review-item
phase fact as evidence.

I CORRECTED THE PLAN'S OWN SECURITY REASONING IN BOTH DIRECTIONS, WHICH IS THE PART I WOULD MOST WANT
A SECOND READER TO CHECK. In one direction the plan gives too much credit to the per-token check
(PR-1004): the regex ALONE already refuses `x /srv/y`, `a ~/b` and `x ../y`, because a space-separated
continuation token must begin with `[A-Za-z0-9()]`. Of the listed cases the per-token guard is
load-bearing for exactly one, the Windows `x C:/Users/<name>`, which the regex admits. I kept the
guard and recorded the correct attribution, because a future reader told the wrong reason is exactly
the reader who deletes it. In the other direction the plan claims too much for the whole widening
(PR-1005): OQ-01 answered "does this weaken the boundary" with a flat "not if the path checks are
kept", and that is false as stated. Measured, a bare maintainer handle (no path, no separator) IS
admitted by the new rule and IS flagged by the shipped leak sanitizer as rule `handle`, as is
`Gemini 3.8 Flash (High) <handle>`. The path class stays refused and is genuinely tightened, which is
what `_LABEL_RE`'s comment names as the point of the space exclusion; but a non-path identifier is now
admissible on this key. I did NOT reject the plan over it: the value is host-supplied on both read
paths, never human free text, and the alternative is the defect. I made it explicit in E-04, in
OQ-01, and in the approval gate, and I added the sentence a human needs in order to refuse: if you
will not accept that trade, the producer-normalization route is the alternative and this plan should
not be approved as written. That is the maintainer's call, not mine.

TWO SMALLER THINGS THAT PREVENT FALSE TEST EXPECTATIONS. `model` is in `ALLOWED_METRIC_KEYS` and NOT
in `ALLOWED_EVENT_KEYS` (verified), and `_metric_payload` omits the key entirely when the model is
empty, so E-05 case (1)'s "every non-event grain" wording is right and case (5) should assert the key
is ABSENT rather than empty; I recorded both so an executor does not "strengthen" case (1) into a
failing assertion. And there is a THIRD `_LABEL_RE` in `run_analytics_schema` which is NOT a gate on
`Fact.model` (`Fact` has no `__post_init__` validating it), so two surfaces really is the complete
set and no third refusal will surprise anyone (F-12, INFO).

WHAT I DID NOT CHANGE. The mechanism and its three-part decomposition, which I verified is not
redundant: E-02's fallback alone fixes the oc no-flag case with no label change (there
`cost_attribution.model` is a resolvable id that today's `_LABEL_RE` already accepts) and CANNOT fix
the agy case (where both fields hold the same rejected display name), so E-04 is load-bearing for agy
and E-02 for oc, and neither substitutes for the other. Also unchanged: OQ-02's grain answer (I
confirmed `build_run_facts` merges both phase usages into the IPD grain, so naming one model there
would misattribute the other), both Carrier-Declined deferrals, the `medium` priority, and the
outcomes-only test posture.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1001 | HIGH | IN-SCOPE | G. Plan executability / E. Testing (evidence unobtainable where the plan runs) | Measured from this review's lane: `.aw/records/runs` absent; `run_viewer.discover_run_dirs(Path("."))` -> 0; `discover_run_dirs(runner_shared.runs_repo_root(Path(".")))` -> 283. `.aw/.gitignore` line `records/runs/`. `runner_shared.runs_repo_root` docstring records 0 vs 246 from lane `vddpml`; the `_SESSION_ID_KEYS` comment notes "this lane has no `.aw/records/runs` corpus" | **E-01's CORPUS SURVEY FINDS NOTHING FROM A LANE, AND ZERO LOOKS EXACTLY LIKE "NO DEFECT".** The runs tree is gitignored and an execute turn is isolated by default, so a CWD-relative glob returns no runs. The executor could have reported the premise unreproducible and skipped the entire fix, or recorded "0 runs" as evidence the bug was gone. The repository already ships the resolver for this and documents the trap twice. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now mandates `runner_shared.runs_repo_root` (or `discover_run_dirs` under it), forbids reading 0 as absence, requires the corpus-independent parts (b)/(c) to be produced regardless, and permits a LABELLED synthetic substitute for (a). V-01 now requires the resolved root and run count as evidence. Added F-7, and named the survey as the first of three easiest-to-fake claims in the gate. |
| PR-1002 | MEDIUM | IN-SCOPE | C. Architecture / G (an instruction that cannot be satisfied) | A lazy import enters `sys.modules` on first call, so the prescribed before/after check is call-order dependent. Measured: `import agent_workflows.run_analytics` leaves `runner_shared` ABSENT; `runner_shared.py` 32452 lines vs `run_analytics.py` 888; two-module import 118ms -> 166ms (min of 3) | **E-02's IMPORT INSTRUCTION CONTRADICTS ITS OWN VERIFICATION.** It told the executor to import the key (lazily if needed) AND to keep `runner_shared` out of the import graph, which a lazy import does not do once the function runs. The underlying concern is real and measurable, so the instruction needed replacing rather than deleting. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now defines `_COST_ATTRIBUTION_KEY = "cost_attribution"` locally with a comment naming `runner_shared.COST_ATTRIBUTION_KEY` as the mirrored contract, and E-05 gains case (7) asserting the two are equal with the import inside the TEST. V-02 requires the post-change `sys.modules` check to print `False` and the diff to show no import, lazy or otherwise. Added F-8; the import claim is named as an easiest-to-fake claim in the gate. |
| PR-1003 | MEDIUM | IN-SCOPE | A. Correctness (a phase the plan's wording does not account for) | The loop's first entry is `Phase.EXECUTE if item_phase is Phase.EXECUTE else item_phase`; `run_analytics._phase_of` returns `Phase.REVIEW` for `action == "review"` | **THE "EXECUTE" LOOP ENTRY IS NOT ALWAYS `Phase.EXECUTE`.** E-03 described the loop as `(Phase.EXECUTE ..., exec_usage), (Phase.VERIFY, verify_usage)` and told the executor to bind the verifier model to the VERIFY entry. An implementation keying off the loop variable could also catch `Phase.REVIEW`, silently crediting a review item's measurement to the verifier's model. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states the real first-entry expression, instructs binding the SECOND entry or carrying the model in the loop tuple, and adds the review-item case to its expected outcome. V-03 requires a review-item phase fact as evidence. Added F-9. |
| PR-1004 | MEDIUM | IN-SCOPE | B. Security (a correct guard defended by a wrong reason) | Per-case guard attribution driven at review: `x /srv/y`, `a ~/b`, `x ../y` all give `regex=False`; `x C:/Users/<name>` gives `regex=True, whole_path=False, token_path=True` | **THE PER-TOKEN CHECK IS CREDITED WITH WORK THE REGEX ALREADY DOES, WHICH IS HOW A GUARD GETS DELETED LATER.** E-04 justifies the per-token path check with `_looks_like_path("x /srv/y") == False`, but the proposed regex refuses that input on its own (a continuation token must start with `[A-Za-z0-9()]`). The guard IS still needed, for the Windows drive path after a space, which the regex admits. A reader who checks the stated reason, finds it redundant, and simplifies would remove the only guard covering that case. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-04 now attributes each guard correctly, says explicitly to KEEP both the per-token check (naming its one load-bearing case) and the whole-string check, and forbids simplifying on the "regex already handles it" premise. V-04 now requires per-refusal guard attribution as evidence, which also proves no guard is dead. Added F-10. |
| PR-1005 | MEDIUM | IN-SCOPE | B. Security / F (an over-claim in the plan's own privacy answer) | Driven against `leak_sanitizer.build_ruleset(Path.cwd())` with a runtime-composed handle: the bare handle is ADMITTED by the new rule and flagged `handle` by the sanitizer; so is `Gemini 3.8 Flash (High) <handle>`. The path class (`/home/<name>/...`, `x /home/<name>/...`) is refused by the rule | **OQ-01 ANSWERS "DOES THIS WEAKEN THE BOUNDARY" WITH A FLAT NO, AND THAT IS NOT TRUE.** Admitting spaces admits a non-path IDENTIFIER on the `model` key. The path class is genuinely refused and tightened, so the plan's reasoning is right about what it measured and wrong about what it concluded. Left as authored, a human approves a privacy widening whose actual cost is not stated anywhere in the plan. | C:Low; U:Medium; S:Medium; F:Low; Overall:Medium | FIXED | Not by narrowing the rule (that would re-break the defect) but by STATING the limit and bounding it: OQ-01 rewritten to separate the proven path-class claim from the accepted identifier-class narrowing, E-04 carries the measurement and requires the `_MODEL_LABEL_RE` comment to state it, the gate gains a "THE PRIVACY DECISION YOU ARE ACTUALLY MAKING" paragraph naming the producer-normalization alternative and saying the plan should not be approved as written by a human unwilling to accept the trade, and E-06/V-06 now forbid presenting the green leak-detector test as proof of the stronger claim. Added F-11. Bounded by provenance: `model` is written only from `options.model` / `cost_attribution.model`, both host-supplied. |
| PR-1006 | LOW | IN-SCOPE | E. Testing (assertions that would fail against a correct implementation) | `model` in `privacy.ALLOWED_METRIC_KEYS` -> True; in `ALLOWED_EVENT_KEYS` -> False; `project_run_facts` routes EVENT through `project_event_facts`; `_metric_payload` guards with `if fact.model:` | **TWO E-05 CASES COULD BE "STRENGTHENED" INTO FAILURES.** Case (1) says every non-event grain, which is correct only because the event allowlist excludes `model`; an executor who did not know that might extend it to the event grain and fail against correct code. Case (5) asserts `model == ""` from `build_run_facts`, but the PROJECTED payload omits the key entirely, so an assertion that it is present-and-empty would also fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now records the allowlist asymmetry with the measurement, says case (1)'s wording is deliberate and must not be widened, and directs case (5) to assert the key is ABSENT from the projected payload. V-07 adds that the post-change grain set must show no model on the event grain and that this is correct by design. |
| PR-1007 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Gate as authored: an UNCONDITIONAL "the terminal transition is `aw ipd finalize` (the runner owns it in a lane)", a fence listing only changed paths, one stop condition, and "its release gate is preserved by that handoff" with no evidence. `evaluate_blocking_close(lixqyc, "done")` today -> `legitimate=False`, "the work has not shipped (carrier is not executed/implemented)" | **THE GATE UNDERSPECIFIED THREE THINGS AND ASSERTED A FOURTH WITHOUT EVIDENCE.** Finalize ownership was stated unconditionally rather than runner-or-executor; the fence named no expected-unmodified paths, so reconciliation had little to check; there was one stop condition where the premise-change case also warrants one; and the `lixqyc` close was asserted as preserved when the predicate REFUSES it until this plan is executed, which an executor could read as licence to close it early. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Finalize now carries conditional runner/executor ownership and forbids a raw `git mv`. The fence names four expected-unmodified surfaces (`runner_shared.py`, `run_analytics_schema.py`, the event allowlist, `CORPUS_BASELINE`/the query caveat). A second stop condition covers the defect no longer reproducing. The close paragraph now states the measured refusal, that `graduated` is the correct interim state, and forbids pre-closing or de-gating. A "WHAT THIS DOES NOT CHANGE" paragraph lists the stale caveat a user will still see. |
| PR-1008 | LOW | IN-SCOPE | A. Correctness (unlabelled provenance of a measurement) | This review ran in a lane with no runs corpus (PR-1001), so the "5 of 24" and "0 runs carry `verify_cost_attribution`" counts could not be re-counted; all four code defects WERE re-driven directly | **THE FINDINGS TABLE PRESENTS CORPUS COUNTS AND CODE FACTS AS ONE CLASS OF EVIDENCE.** They are not: the code facts are reproducible anywhere, and the counts are reproducible only where the corpus lives. A later reader re-checking the table from a lane would fail to reproduce half of it and could wrongly conclude the findings were wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Findings preamble now states which findings were re-verified at review and how, and separates the corpus colour from the code defects explicitly ("the counts are corpus colour; the defects are in the functions"). Also records a third `_LABEL_RE` exists in `run_analytics_schema` and is NOT a gate on `Fact.model` (F-12), so the two-surface claim is complete. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-1005: the widening admits a non-path identifier. Narrow the rule, reject the plan, or accept and state the limit? | ACCEPT AND STATE IT, bounded by provenance, and give the human the refusal path explicitly. | (a) Narrow the rule to refuse any identifier-looking token: rejected, it cannot be done without refusing the display name itself (the sanitizer's `handle` rule matches a bare word, and `Gemini`-style tokens are bare words), so it would re-break the defect being fixed. (b) REPLAN onto producer normalization: rejected as a reviewer decision, because the backlog item explicitly scopes this as a CONSUMER change and the maintainer's own framing put the producer out of fence; but recorded in the gate as the alternative a human may choose. (c) Accept silently, as authored: rejected, a human approving a privacy widening is entitled to know its cost, and the plan's flat "no" was measurably wrong. | The admitted-handle measurement against the shipped ruleset; `_LABEL_RE`'s comment naming command lines and paths as the target; the two host write paths for `model` (`options.model`, `cost_attribution.model`), both host-supplied; backlog `lixqyc`'s "this is a CONSUMER change" scope note | yes |
| D-2 | PR-1002: how should `run_analytics` learn the cost-attribution key without importing the 32k-line runner? | LOCAL CONSTANT plus a key-agreement assertion in the test. | (a) Module-level import: rejected on the measurement (48ms, and it pulls the runner into the analytics import graph, which the plan itself wanted to avoid). (b) Lazy import as authored: rejected, it does not achieve the stated property and makes the verification call-order dependent, so the plan would have shipped an unsatisfiable check. (c) Local constant with NO test: rejected, that is exactly the silent-drift shape the repo's single-source-of-truth principle warns about; the assertion costs one line and turns drift into a failure. | The `sys.modules` measurement before/after; the line counts and import timing; the existing precedent of pinning cross-module string contracts by test | yes |
| D-3 | PR-1004: the per-token path check's stated reason is mostly redundant. Drop the guard or keep it? | KEEP IT, and correct the reason. | (a) Drop it and rely on the regex: rejected on measurement, it is the only guard refusing `x C:/Users/<name>`, which the regex admits. (b) Keep it and leave the wrong reason: rejected, a guard defended by a reason a reader can falsify is a guard that gets deleted in the next cleanup. | Per-case guard attribution driven at review across seven inputs | yes |
| D-4 | PR-1001: E-01 cannot survey the corpus from a lane. Should the item be marked blocked, or made lane-aware? | MAKE IT LANE-AWARE with the shipped resolver, and require the resolved root plus run count as evidence. | (a) Mark E-01 blocked pending a non-isolated run: rejected, it would stall a plan whose other six items are fully executable in a lane, and the resolver exists precisely so this is not a blocker. (b) Drop the corpus survey and rely on fixtures: rejected, the survey is what distinguishes a live defect from a theoretical one, and the plan's HIGH findings rest on it. (c) Leave the glob: rejected outright, because zero results are indistinguishable from "defect absent" and the plausible outcome is a skipped fix. | `discover_run_dirs` 0 (lane) vs 283 (resolved); `.aw/.gitignore` `records/runs/`; `runs_repo_root`'s own docstring recording the same 0-vs-246 measurement | yes |

### Deferred and open

- (none). All eight findings are FIXED in place. PR-1005 is the one whose FIX is a disclosure rather
  than a code change, and that is deliberate and reasoned: narrowing the rule would re-break the
  defect, so the honest remedy is to state the accepted cost, bound it by provenance, and give the
  approving human the alternative and the standing to refuse. Under the Fix Bar nothing this plan is
  responsible for was left unfixed. No finding sits at or above the repository gate threshold
  (`HIGH`) and unfixed, so no escalation to a `- Blocking: yes` question is owed (PR-1001 is HIGH and
  is FIXED). Both pre-existing open questions were already resolved by the author; OQ-01's answer was
  materially corrected here rather than accepted, OQ-02's was confirmed against the merge code, and
  both gained a Carrier-Declined. One question I deliberately did NOT decide is recorded as D-1's
  option (b): whether the maintainer would rather normalize the display name at the producer than
  widen the label. That is a scope and risk-appetite call, it is now stated in the approval gate where
  a human will see it before signing, and no code change depends on it.
