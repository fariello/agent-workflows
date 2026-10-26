# IPD: Add the Review-Depth field, pre-pass tier facts, and run-state recording of the tier and its answers

- Date: 2026-10-24
- Kind: child
- Concern: Spec `k3yx72` (approved) has the review agent rate each plan's review tier (`simple`, `standard`, `complex`) after answering five recorded tier questions (Section 5.2, MD-1). Three pieces it needs do not exist. (1) The plan has nowhere to store the tier: `ipd_schema.META_RECOGNIZED` has no `Review-Depth` field, so writing one makes `aw ipd lint` report an unknown field (`IPD-M103`). (2) The runner collects none of the facts the tier questions ask about (Section 4.1 item 4), so the agent must search for them, which costs model steps (Section 1 problem 1). (3) Run state records no tier and no answers, so the analytics the spec relies on (Section 5.2, "records the tier and the five answers in run state") cannot compare tiers with outcomes.
- Scope: Register `- Review-Depth:` as a recognized, optional, closed-enum plan field; add a pure function that computes the pre-pass tier facts from a plan's text; add a pure parser for the `AW-TIER:` reply marker and for the five tier answers in a review record's `### Step T` subsection; add a run-state recorder that writes the tier, its source, and the answers onto the current review attempt; and carry the tier into the attempt-grain analytics. EXCLUDES sending prompts, deciding when to call the recorder, and the re-ask on a malformed marker (all Order 04); EXCLUDES writing `- Review-Depth:` into a plan (S7's job, Order 01 step file plus Order 04 postcondition).
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/review_tier.py, agent_workflows/run_dashboard.py, agent_workflows/run_dashboard_assets/dashboard.js, agent_workflows/run_analytics_attempts.py, docs/run-analytics.md, .aw/records/plans/README.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, tests/test_review_tier.py, tests/test_run_analytics_review_cost.py, tests/test_ipd_schema.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Set: revsteps
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: gv3smb

## Workflow history
- 2026-10-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: gv3smb verified (set revsteps, attempt 1). [Scope reconciliation - widened-scope tests/test_ipd_schema.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-10-25 approved (aw set): status set to approved
- 2026-10-25 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED
- 2026-10-25 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED; review record .aw/records/reviews/20261024-revsteps-02-gv3smb-add-the-review-depth-field-pre-pass-tier-facts-and-run-state.review.md
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give the multi-prompt review (Order 04) a place to store the tier, the facts to hand the agent, a parser for the agent's tier answer, and a recorder so every review's tier and answers are in run state for later analysis.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the plan field

- [x] E-01 In `agent_workflows/ipd_schema.py`, add `META_REVIEW_DEPTH = "Review-Depth"` and `REVIEW_DEPTH_VALUES: FrozenSet[str] = frozenset(("simple", "standard", "complex", "orchestrator"))` beside the `META_ATTENDED` block, add `META_REVIEW_DEPTH` to the tuple that builds `META_RECOGNIZED`, and in `validate_metadata` (where the `attended` check lives; `parse_metadata_block` only records duplicate and unknown fields) add a `MetaError` for a present value outside `REVIEW_DEPTH_VALUES`, so `ipd_lint.check_metadata` reports it as `IPD-M104`. Absence is silent, so no existing plan is affected. `orchestrator` is included because spec Section 5.1 gives every Order-00 plan a fixed profile, and S7 records that profile like any tier. The field is not added to `ipd_lifecycle.frozen_region_digest`, which covers only `- Scope-Paths:` and E/V action text (spec Section 7.2).
  - Depends on: none
  - Expected outcome: a plan with `- Review-Depth: standard` lints with no `IPD-M103`; `- Review-Depth: huge` reports `IPD-M104`.
  - Execution state: performed

- [x] E-02 Document the field: in `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 4.4 "The metadata block", add one paragraph for the optional field `Review-Depth` (closed enum `simple`/`standard`/`complex`/`orchestrator`; written once per review by the review's finalize step; not part of the reviewed contract; source spec `k3yx72` Section 7.2), worded like the existing `Attended` paragraph, and append a `## Workflow history` note line. In `.aw/records/plans/README.md`, add one sentence beside the `Readiness` field description naming `Review-Depth` and its writer.
  - Depends on: E-01
  - Expected outcome: both documents name the field and its four values.
  - Execution state: performed

### Task group 2: tier facts and parsers

- [x] E-03 Create `agent_workflows/review_tier.py` with `tier_facts(plan_text: str) -> dict`, a pure function built on `ipd_lint.parse`, returning: `kind` (from `- Kind:`), `scope_paths` (the `- Scope-Paths:` list, or `None` when absent or `TODO`), `names_spec` (true when any scope path ends in `.spec.md`), `e_items` (count of `E-*` leaves), `task_groups` (count of task-group H3s, the `ParsedDoc.exec_task_groups` value), `exceeds_size` (`ipd_schema.size_warning(task_groups, e_items)`), and `in_set` (true when `- Set:` is present). Add `render_tier_facts(facts) -> str`, a short Markdown block the runner puts into prompt 1 (spec Section 4.1 item 6), one line per fact.
  - Depends on: none
  - Expected outcome: `tier_facts` returns the seven keys for any plan text and never raises; on a malformed plan the parsed counts are 0 (what `ipd_lint.parse` returns: measured at review, `parse('')` gives `meta_fields={}`, `exec_task_groups=0`, no leaves) and `kind`/`scope_paths` are `None`.
  - Execution state: performed

- [x] E-04 In `review_tier.py`, add `parse_tier_marker(reply_text: str) -> str | None`: the last non-empty line of the reply, after ignoring a trailing code-fence line and stripping that line's leading and trailing whitespace, must equal exactly `AW-TIER: simple`, `AW-TIER: standard`, or `AW-TIER: complex` (case-sensitive), and the function returns the tier, else `None` (spec `k3yx72` Section 6 row T and Section 8.1 rules 1 and 2, applied to this marker; `k3yx72` AC-08). Add `parse_tier_answers(review_text: str) -> dict[int, str] | None`: find the last `## Round <n>` section, then its `### Step T` subsection, and return the answers to questions 1 to 5, read as lines starting with `1.` to `5.` (or `Q1:` to `Q5:`); return `None` when the subsection is absent. Add `tier_answers_complete(answers) -> bool` (all five present and non-empty), which Order 04's postcondition for check T calls.
  - Depends on: none
  - Expected outcome: `parse_tier_marker("text\nAW-TIER: standard\n```\n")` returns `"standard"`; `parse_tier_marker("aw-tier: simple")` returns `None`; `parse_tier_answers` on a two-round review returns the last round's answers; none of the three reads files or mutates its input.
  - Execution state: performed

### Task group 3: run state and analytics

- [x] E-05 In `review_tier.py`, add `record_review_tier(attempt: MutableMapping, *, tier: str | None, source: str, answers: Mapping[int, str] | None, facts: Mapping | None) -> None`, which writes `attempt["review_tier"]` (one of `REVIEW_DEPTH_VALUES`, or `None`; any other value raises `ValueError`, so a caller bug cannot record a tier the plan field would refuse), `attempt["review_tier_source"]` (`"agent"` for a marker-chosen tier, `"orchestrator"` for the fixed profile, `"raised"` when the agent raised it later per spec Section 5.3; any other source raises `ValueError`), `attempt["review_tier_answers"]` (a dict with string keys `"1"` to `"5"`, JSON-safe), and `attempt["review_tier_facts"]`. It never changes the tier it is given: spec `k3yx72` MD-1 says the runner forces no tier (`k3yx72` AC-08). Order 04 calls it; this plan only provides it.
  - Depends on: E-03, E-04
  - Expected outcome: after a call, the attempt dict carries the four keys and `json.dumps(attempt)` succeeds; an unknown tier or source raises `ValueError`.
  - Execution state: performed

- [x] E-06 Carry the tier into the attempt grain: in `run_dashboard.collect_rows` add a `review_tier` row value to BOTH attempt `base` dicts (the recorded-attempt dict, which reads the attempt's `review_tier` when a non-empty string and `""` when the key is missing or `None`, and the synthesized-attempt dict, which is always `""`), add `review_tier` to `COLUMNS` and `ATTEMPT_FACT_FIELDS`, and bump `ATTEMPT_FACTS_SCHEMA_VERSION` by one; in `run_analytics_attempts` add `review_tier` to `ATTEMPT_FILTER_FIELDS` and `ATTEMPT_GROUP_FIELDS`. In `run_dashboard_assets/dashboard.js` add `review_tier` to the list of fields normalized to `(none)`, to `DIMS` (label `Review tier`, help text naming `simple` / `standard` / `complex` / `orchestrator`, recorded for plan reviews run with `--review-mode steps` only), to `FACETS`, and to `GROUPABLE`. This follows the `readiness` addition of plan `avg8qv` (its E-03, E-04 and E-06). In `docs/run-analytics.md` section "Review cost: per-attempt analysis", add the row `| Attempts by review tier | aw runs query attempts --filter action=review --group-by review_tier --metric cost,steps |` and remove nothing from "What is not recorded yet" (review steps stay listed until Order 04).
  - Depends on: E-05
  - Expected outcome: `aw runs query attempts --group-by review_tier` is accepted, and `aw runs query schema` lists `review_tier`.
  - Execution state: performed

### Task group 4: tests and commit

- [x] E-07 Add `tests/test_review_tier.py`, marked `core`, covering: (a) `ipd_lint.lint_text` on a minimal conformant plan with `- Review-Depth: standard` reports no `IPD-M103`/`IPD-M104`, and with `huge` reports `IPD-M104`; (b) `ipd_lifecycle.frozen_region_digest` is equal for the same plan with and without the field; (c) `tier_facts` on three fixture plans (one naming a `.spec.md`, one with 19 E-items, one with no `- Scope-Paths:`) returns the expected values; (d) `parse_tier_marker` accepts each valid marker, accepts it before a trailing fence line, and returns `None` for `aw-tier: simple`, a marker that is not on the last line, and an unknown tier; (e) `parse_tier_answers` on a review text with two rounds reads the last round only and `tier_answers_complete` is false when answer 4 is missing; (f) `record_review_tier` writes the four keys, passes the tier through unchanged (spec `k3yx72` MD-1), the result survives `json.dumps`, and an unknown tier or source raises `ValueError`; (g) the attempt-grain round trip: a fixture run whose attempt carries `review_tier: "simple"`, analyzed by the real `aw runs analyze` leaf, answers `run_query("attempts", group_by="review_tier", ...)` with a `simple` row, and an attempt with no `review_tier` key lands in the `""`/`(none)` group rather than being dropped (reuse `_review_run` and the `AttemptQueryTests` setup of `tests/test_run_analytics_review_cost.py`, adding a `review_tier` keyword the way `avg8qv` E-05 added `readiness`); (h) `tier_facts` on an empty string and on a plan with no metadata block returns the seven keys without raising.
  - Depends on: E-01, E-03, E-04, E-05, E-06
  - Expected outcome: a passing core test module that calls the real functions and CLI leaf.
  - Execution state: performed

- [x] E-08 Add one `CHANGELOG.md` entry (plans may record `- Review-Depth:`; review attempts can record their tier, queryable by `--group-by review_tier`), no em or en dashes. Run `python3 -m pytest -o addopts="" -n auto tests/test_review_tier.py tests/test_ipd_lint.py tests/test_ipd_schema.py tests/test_run_analytics_review_cost.py tests/test_run_dashboard.py`, the bare core gate `python3 -m pytest`, and `aw check`; commit through `aw commit gv3smb -- <each changed path>`. Never push.
  - Depends on: E-02, E-07
  - Expected outcome: both pytest runs pass; `aw check` reports no error and no warning this plan introduced; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- New optional metadata fields follow the `Coverage` and `Attended` precedent in `ipd_schema.py`: a `META_*` constant, membership in `META_RECOGNIZED`, and a closed-enum check in `parse_metadata_block` that lint reports as `IPD-M104`.
- Attempt-grain analytics fields follow plan `avg8qv` (executed): row value in `run_dashboard.collect_rows`, `COLUMNS`, `ATTEMPT_FACT_FIELDS`, a schema-version bump, and the two allowlists in `run_analytics_attempts`.
- `ipd_schema.size_warning` (limits `MAX_TASK_GROUPS = 5`, `MAX_E_LEAVES = 18`) is the existing size signal; `tier_facts` reuses it rather than defining new limits.
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n "Review-Depth" agent_workflows` returns nothing | The field does not exist. |
| F-02 | `ipd_schema.META_RECOGNIZED` docstring context: unknown fields are errors for new IPDs | Writing the field before registering it fails lint, so this plan must land before any review writes it (Order 04 depends on this plan). |
| F-03 | `runner_shared.add_run_label_flags`: `--review-variant` is "no behavior change" | Run state already records the variant label; the tier is per attempt, so it belongs on the attempt, not in `options`. |
| F-04 | Spec `k3yx72` Section 5.2 measurement: 167 of 1,554 plans edit a `.spec.md`, 1 exceeds size limits | `names_spec` and `exceeds_size` are cheap facts with real spread, so supplying them saves searches. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: register and document `Review-Depth`.
2. E-03, E-04: pure fact and parser functions.
3. E-05, E-06: recorder and analytics.
4. E-07, E-08: tests, changelog, gates, commit.

## Deferred / out of scope (with reason)

- Calling `tier_facts` and `record_review_tier` from the runner: Order 04 owns the review sequence.
  - Carrier: uiyoax
- Storage under metadata spec `4sd62s` (event logs): spec `k3yx72` Section 12 requires the `4sd62s` migration to carry `Review-Depth` like any other field if this lands first; nothing is owed here.
  - Carrier-Declined: owed by the `4sd62s` migration, not by this plan; spec `k3yx72` Section 12 states the obligation on that migration.

## Scope check

- Over-scope: none.
- Under-scope: none. Spec Sections 4.1 item 4, 5.2 (recording), 7.2 (field) and 12 (field naming) are covered. This plan targets today's front-matter storage (spec `k3yx72` Section 12 requires the format be declared): `- Review-Depth:` is a front-matter field, not a `4sd62s` event.

## Required tests / validation

- Field accepted, bad value refused, digest unchanged: E-07 (a), (b).
- Facts and parsers correct on edge cases: E-07 (c) to (e).
- Recorder and analytics round trip: E-07 (f), (g).
- Commands: E-08 named run, bare core gate, `aw check`, summaries pasted.

## Spec / documentation sync

Amends spec `20260802-1904` (IPD structure and linting) Section 4.4 with the new optional field, declared in `- Scope-Paths:`. Why: that section is the list of recognized metadata fields, and an undocumented recognized field is the drift it exists to prevent. `docs/run-analytics.md` and `.aw/records/plans/README.md` gain one line each. Spec `k3yx72` already describes the field and needs no edit.

## Open questions

### OQ-01: Include `orchestrator` as a `Review-Depth` value?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. Spec Section 5.1 gives orchestrators a fixed profile that check T does not rate, and S7 writes the field for every review; without the value S7 would have to omit the field for orchestrators, which makes "absent" ambiguous between "never reviewed under this design" and "orchestrator". Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `git diff` hunk of `agent_workflows/ipd_schema.py` adding `META_REVIEW_DEPTH`, `REVIEW_DEPTH_VALUES`, the `META_RECOGNIZED` entry, and the enum check in `validate_metadata`; and `aw ipd lint --phase author --agent` output on two scratch copies of this plan, one with `- Review-Depth: standard` (no `IPD-M103`/`IPD-M104`) and one with `- Review-Depth: huge` (`IPD-M104`).
  - Observed evidence:
```diff
diff --git a/agent_workflows/ipd_schema.py b/agent_workflows/ipd_schema.py
@@ -354,6 +354,13 @@ META_SCOPE_EXCEEDED = "Scope-Exceeded"
 META_ATTENDED = "Attended"
 ATTENDED_REQUIRED = "required"
+# `- Review-Depth: <simple | standard | complex | orchestrator>` (spec k3yx72 Section 7.2;
+# Set revsteps, IPD gv3smb). Written once per review by the review's finalize step (S7).
+# Recognized but OPTIONAL; absent means no tier has been recorded.
+META_REVIEW_DEPTH = "Review-Depth"
+REVIEW_DEPTH_VALUES: FrozenSet[str] = frozenset(
+    ("simple", "standard", "complex", "orchestrator")
+)

 # The full set of recognized field names (unknown fields are errors for new IPDs).
 META_RECOGNIZED: FrozenSet[str] = frozenset(
@@ -376,6 +383,7 @@ META_RECOGNIZED: FrozenSet[str] = frozenset(
         META_COVERAGE_CHECKED,
         META_SCOPE_EXCEEDED,
         META_ATTENDED,
+        META_REVIEW_DEPTH,
     )
 )

@@ -497,6 +505,17 @@ def validate_metadata(
             MetaError(
                 META_ATTENDED, f"invalid value (only '{ATTENDED_REQUIRED}' is accepted)"
             )
         )

+    # Review-Depth (revsteps gv3smb E-01; spec k3yx72 Section 7.2): OPTIONAL, so absence is silent;
+    # but a PRESENT value outside the closed enum is an error, reported by `ipd_lint.check_metadata`
+    # as IPD-M104.
+    review_depth = fields.get(META_REVIEW_DEPTH)
+    if (
+        review_depth is not None
+        and review_depth.strip() not in REVIEW_DEPTH_VALUES
+    ):
+        errors.append(
+            MetaError(
+                META_REVIEW_DEPTH,
+                "unrecognized review-depth value (expected one of "
+                + ", ".join(sorted(REVIEW_DEPTH_VALUES))
+                + ")",
             )
         )
```
Scratch standard copy lint:
`{"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"findings_by_severity":{"error":0,"warning":0,"info":1},"evidence":["plans-lint"],"diagnostics":[{"location":"scratch/scratch-standard.ipd.md","rule":"IPD-Z602"}],"next":null}`
Scratch huge copy lint:
`{"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":2,"findings_by_severity":{"error":1,"warning":0,"info":1},"evidence":["plans-lint"],"diagnostics":[{"location":"scratch/scratch-huge.ipd.md","rule":"IPD-M104"},{"location":"scratch/scratch-huge.ipd.md","rule":"IPD-Z602"}],"next":null}`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` of the structure-and-linting spec Section 4.4 paragraph and its history line, and of `.aw/records/plans/README.md`.
  - Observed evidence:
```diff
diff --git a/.aw/records/plans/README.md b/.aw/records/plans/README.md
--- a/.aw/records/plans/README.md
+++ b/.aw/records/plans/README.md
@@ -66,6 +66,8 @@ has run and honestly declined to conclude (leaving the plan at `Status: to-revie
 `(to-review, absent)` state may therefore be one no reviewer has opened or one a review examined and
 could not conclude on, and a reader cannot tell which from the field alone.

+A plan may also carry the optional, recognized `- Review-Depth: <simple | standard | complex | orchestrator>` field, written once per review by `/plan-review`'s finalize step.
+
diff --git a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
--- a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
+++ b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
@@ -151,6 +151,8 @@ Recognized-but-optional fields (all IPDs): `Scope-Paths` (Section 4.5), `Priorit

 Optional field: `Attended` (amended 2026-10-17, direct fix, no plan). ...

+Optional field: `Review-Depth` (amended 2026-10-25, plan `gv3smb`, Set `revsteps`, Order 02; source spec `k3yx72` Section 7.2). Closed enum `simple`, `standard`, `complex`, or `orchestrator`. Written once per review by the review's finalize step; not part of the reviewed contract. Validated as a recognized metadata field (`META_RECOGNIZED`), where any value outside the closed enum is a metadata error (`IPD-M104`). Absence is silent.
+
@@ -837,6 +839,7 @@ After the IPD-system Set lands:

 ## Workflow history

+- 2026-10-25 note (aw specs): Section 4.4 amended (revsteps gv3smb E-02): document optional field - Review-Depth: with closed enum simple/standard/complex/orchestrator, written by review finalize step (source spec k3yx72 Section 7.2).
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `python3 -c` output calling `review_tier.tier_facts` on this plan file's own text, showing all seven keys and their values.
  - Observed evidence:
```python
{'e_items': 8,
 'exceeds_size': False,
 'in_set': True,
 'kind': 'child',
 'names_spec': True,
 'scope_paths': ['agent_workflows/ipd_schema.py',
                 'agent_workflows/review_tier.py',
                 'agent_workflows/run_dashboard.py',
                 'agent_workflows/run_dashboard_assets/dashboard.js',
                 'agent_workflows/run_analytics_attempts.py',
                 'docs/run-analytics.md',
                 '.aw/records/plans/README.md',
                 '.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md',
                 'tests/test_review_tier.py',
                 'tests/test_run_analytics_review_cost.py',
                 'tests/test_ipd_schema.py',
                 'CHANGELOG.md'],
 'task_groups': 4}
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_tier.py -k "marker or answers"` with every selected test PASSED.
  - Observed evidence:
```
tests/test_review_tier.py::test_parse_tier_answers_two_rounds PASSED     [ 50%]
tests/test_review_tier.py::test_parse_tier_marker PASSED                 [100%]

======================= 2 passed, 6 deselected in 0.47s ========================
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_tier.py -k record` with every selected test PASSED, and quote the assertion that the recorded tier equals the tier passed in.
  - Observed evidence:
```
tests/test_review_tier.py::test_record_review_tier PASSED                [100%]

======================= 1 passed, 7 deselected in 0.51s ========================
```
Quoted assertion:
`assert attempt["review_tier"] == "standard"` (matching `tier="standard"` argument to `record_review_tier`).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `git diff` hunks in `run_dashboard.py` (both `base` dicts, `COLUMNS`, `ATTEMPT_FACT_FIELDS`, the version bump), `run_dashboard_assets/dashboard.js`, and `run_analytics_attempts.py`, and `aw runs query schema --json` output filtered to show `review_tier` in `data.payload.attempt_grain.filter_fields` and `group_by_fields`.
  - Observed evidence:
```diff
diff --git a/agent_workflows/run_dashboard.py b/agent_workflows/run_dashboard.py
@@ -1494,6 +1494,10 @@ def collect_rows(
                 else:
                     att_readiness = ""
+                raw_rt = att.get("review_tier")
+                att_review_tier = (
+                    raw_rt if (isinstance(raw_rt, str) and raw_rt) else ""
+                )
                 base = {
                     "run": run_id,
@@ -1509,6 +1513,7 @@ def collect_rows(
                     "disposition": str(disposition or "(none)"),
                     "verification": str(verification or ""),
                     "readiness": att_readiness,
+                    "review_tier": att_review_tier,
                     "item_status": str(item.get("status") or ""),
@@ -1597,6 +1602,7 @@ def collect_rows(
                     "disposition": "(none)",
                     "verification": "",
                     "readiness": "",
+                    "review_tier": "",
                     "item_status": "",
@@ -1686,6 +1692,7 @@ COLUMNS: tuple[str, ...] = (
         "verification",
         "readiness",
+        "review_tier",
         "item_status",
@@ -1833,6 +1840,7 @@ ATTEMPT_FACT_FIELDS: tuple[str, ...] = (
     "verification",
     "readiness",
+    "review_tier",
     "item_status",
@@ -1888,3 +1896,3 @@ ATTEMPT_FACT_MAPS: tuple[str, ...] = ("tools", "tool_bytes", "families", "read_
 ATTEMPT_FACTS_FILENAME = "attempts.jsonl"
-ATTEMPT_FACTS_SCHEMA_VERSION = 3
+ATTEMPT_FACTS_SCHEMA_VERSION = 4

diff --git a/agent_workflows/run_dashboard_assets/dashboard.js b/agent_workflows/run_dashboard_assets/dashboard.js
@@ -48,3 +48,3 @@
-    ['set', 'id6', 'kind', 'model', 'host', 'agent', 'phase', 'label', 'review_variant', 'code_commit', 'repo_commit', 'session_origin', 'step_bucket', 'model_source', 'disposition', 'verification', 'readiness', 'item_status', 'action', 'role'].forEach((k) => {
+    ['set', 'id6', 'kind', 'model', 'host', 'agent', 'phase', 'label', 'review_variant', 'code_commit', 'repo_commit', 'session_origin', 'step_bucket', 'model_source', 'disposition', 'verification', 'readiness', 'review_tier', 'item_status', 'action', 'role'].forEach((k) => {
@@ -70,2 +70,3 @@
     readiness: { label: 'Readiness', help: 'go / go-pending-approval / no-go, absent when the review wrote no valid value, recorded for plan reviews only' },
+    review_tier: { label: 'Review tier', help: 'simple / standard / complex / orchestrator, recorded for plan reviews run with --review-mode steps only' },
     action: { label: 'Queue action' },
@@ -85,2 +86,2 @@
-  const FACETS = ['phase', 'stage', 'agent', 'label', 'review_variant', 'session_origin', 'host', 'model', 'outcome', 'restart', 'disposition', 'readiness', 'set', 'token_source'];
-  const GROUPABLE = ['agent', 'phase', 'session_origin', 'step_bucket', 'label', 'review_variant', 'code_commit', 'repo_commit', 'model_source', 'model', 'host', 'stage', 'outcome', 'restart', 'disposition', 'readiness', 'action', 'role', 'set', 'kind', 'verification', 'token_source', 'month', 'week', 'id6', 'run'];
+  const FACETS = ['phase', 'stage', 'agent', 'label', 'review_variant', 'session_origin', 'host', 'model', 'outcome', 'restart', 'disposition', 'readiness', 'review_tier', 'set', 'token_source'];
+  const GROUPABLE = ['agent', 'phase', 'session_origin', 'step_bucket', 'label', 'review_variant', 'code_commit', 'repo_commit', 'model_source', 'model', 'host', 'stage', 'outcome', 'restart', 'disposition', 'readiness', 'review_tier', 'action', 'role', 'set', 'kind', 'verification', 'token_source', 'month', 'week', 'id6', 'run'];

diff --git a/agent_workflows/run_analytics_attempts.py b/agent_workflows/run_analytics_attempts.py
@@ -74,2 +74,3 @@
     "readiness",
+    "review_tier",
     "date",
@@ -99,2 +100,3 @@
     "readiness",
+    "review_tier",
     "set",
```
`aw runs query schema --json` output (filtered to attempt_grain):
```json
"attempt_grain": {
  "filter_fields": [
    "run", "set", "id6", "action", "role", "phase", "attempt", "host",
    "model", "model_source", "agent", "label", "review_variant", "code_commit",
    "repo_commit", "session_origin", "step_bucket", "outcome", "disposition",
    "readiness", "review_tier", "date", "cost_split", "token_source"
  ],
  "group_by_fields": [
    "phase", "action", "role", "host", "model", "model_source", "agent",
    "label", "review_variant", "code_commit", "repo_commit", "session_origin",
    "step_bucket", "outcome", "disposition", "readiness", "review_tier", "set",
    "id6", "attempt", "cost_split", "token_source"
  ]
}
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_tier.py` with every test PASSED and none skipped.
  - Observed evidence:
```
tests/test_review_tier.py::TestAttemptGrainRoundTrip::test_group_by_review_tier_round_trip PASSED [ 12%]
tests/test_review_tier.py::test_parse_tier_answers_two_rounds PASSED     [ 25%]
tests/test_review_tier.py::test_lint_text_review_depth_accepted PASSED   [ 37%]
tests/test_review_tier.py::test_record_review_tier PASSED                [ 50%]
tests/test_review_tier.py::test_tier_facts_fixtures PASSED               [ 62%]
tests/test_review_tier.py::test_parse_tier_marker PASSED                 [ 75%]
tests/test_review_tier.py::test_tier_facts_empty_and_no_metadata PASSED  [ 87%]
tests/test_review_tier.py::test_frozen_region_digest_invariant PASSED    [100%]
============================== 8 passed in 0.70s ===============================
```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the summary lines of the E-08 named pytest run and the bare `python3 -m pytest`, the `aw check` summary compared with the baseline taken before E-01, and the `aw commit` output listing the committed paths.
  - Observed evidence: Named pytest: 171 passed in 26.78s; bare suite: 1842 passed, 11 warnings in 33.11s; aw check: 12 errors (baseline 12), 1 warning (baseline 1), 52 info (0 new errors or warnings).
    E-08 named pytest summary:
    `============================= 171 passed in 26.78s =============================`
    Bare pytest / `aw suite` summary:
    `1842 passed, 11 warnings in 33.11s`
    `aw check` summary compared with baseline:
    Baseline before E-01:
      plans  6   specs  17   prompts  9   research  131   backlog  25   walkthroughs  26   roadmaps  1   comms  1   releases  1   reviews  1287   other  1511
      errors  12   warnings  1   info  51
    Post-implementation:
      plans  6   specs  17   prompts  9   research  131   backlog  25   walkthroughs  26   roadmaps  1   comms  1   releases  1   reviews  1287   other  1511
      errors  12   warnings  1   info  52
    (Zero new errors and zero new warnings introduced).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit gv3smb -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
