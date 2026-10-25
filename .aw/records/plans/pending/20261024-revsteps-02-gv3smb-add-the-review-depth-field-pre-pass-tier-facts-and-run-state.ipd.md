# IPD: Add the Review-Depth field, pre-pass tier facts, and run-state recording of the tier and its answers

- Date: 2026-10-24
- Kind: child
- Concern: Spec `k3yx72` (approved) has the review agent rate each plan's review tier (`simple`, `standard`, `complex`) after answering five recorded tier questions (Section 5.2, MD-1). Three pieces it needs do not exist. (1) The plan has nowhere to store the tier: `ipd_schema.META_RECOGNIZED` has no `Review-Depth` field, so writing one makes `aw ipd lint` report an unknown field (`IPD-M103`). (2) The runner collects none of the facts the tier questions ask about (Section 4.1 item 4), so the agent must search for them, which costs model steps (Section 1 problem 1). (3) Run state records no tier and no answers, so the analytics the spec relies on (Section 5.2, "records the tier and the five answers in run state") cannot compare tiers with outcomes.
- Scope: Register `- Review-Depth:` as a recognized, optional, closed-enum plan field; add a pure function that computes the pre-pass tier facts from a plan's text; add a pure parser for the `AW-TIER:` reply marker and for the five tier answers in a review record's `### Step T` subsection; add a run-state recorder that writes the tier, its source, and the answers onto the current review attempt; and carry the tier into the attempt-grain analytics. EXCLUDES sending prompts, deciding when to call the recorder, and the re-ask on a malformed marker (all Order 04); EXCLUDES writing `- Review-Depth:` into a plan (S7's job, Order 01 step file plus Order 04 postcondition).
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/review_tier.py, agent_workflows/run_dashboard.py, agent_workflows/run_analytics_attempts.py, docs/run-analytics.md, .aw/records/plans/README.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, tests/test_review_tier.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
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
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give the multi-prompt review (Order 04) a place to store the tier, the facts to hand the agent, a parser for the agent's tier answer, and a recorder so every review's tier and answers are in run state for later analysis.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the plan field

- [ ] E-01 In `agent_workflows/ipd_schema.py`, add `META_REVIEW_DEPTH = "Review-Depth"` and `REVIEW_DEPTH_VALUES: FrozenSet[str] = frozenset(("simple", "standard", "complex", "orchestrator"))` beside the `META_ATTENDED` block, add `META_REVIEW_DEPTH` to the tuple that builds `META_RECOGNIZED`, and in `parse_metadata_block` add a `MetaError` for a present value outside `REVIEW_DEPTH_VALUES` (the pattern the `attended` check uses), so lint reports it as `IPD-M104`. Absence is silent. `orchestrator` is included because spec Section 5.1 gives every Order-00 plan a fixed profile, and S7 records that profile like any tier. The field is not added to `ipd_lifecycle.frozen_region_digest`, which covers only `- Scope-Paths:` and E/V action text (spec Section 7.2).
  - Depends on: none
  - Expected outcome: a plan with `- Review-Depth: standard` lints with no `IPD-M103`; `- Review-Depth: huge` reports `IPD-M104`.
  - Execution state: pending

- [ ] E-02 Document the field: in `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 4.4 "The metadata block", add one paragraph for the optional field `Review-Depth` (closed enum `simple`/`standard`/`complex`/`orchestrator`; written once per review by the review's finalize step; not part of the reviewed contract; source spec `k3yx72` Section 7.2), worded like the existing `Attended` paragraph, and append a `## Workflow history` note line. In `.aw/records/plans/README.md`, add one sentence beside the `Readiness` field description naming `Review-Depth` and its writer.
  - Depends on: E-01
  - Expected outcome: both documents name the field and its four values.
  - Execution state: pending

### Task group 2: tier facts and parsers

- [ ] E-03 Create `agent_workflows/review_tier.py` with `tier_facts(plan_text: str) -> dict`, a pure function built on `ipd_lint.parse`, returning: `kind` (from `- Kind:`), `scope_paths` (the `- Scope-Paths:` list, or `None` when absent or `TODO`), `names_spec` (true when any scope path ends in `.spec.md`), `e_items` (count of `E-*` leaves), `task_groups` (count of task-group H3s, the `ParsedDoc.exec_task_groups` value), `exceeds_size` (`ipd_schema.size_warning(task_groups, e_items)`), and `in_set` (true when `- Set:` is present). Add `render_tier_facts(facts) -> str`, a short Markdown block the runner puts into prompt 1 (spec Section 4.1 item 6), one line per fact.
  - Depends on: none
  - Expected outcome: `tier_facts` returns the seven keys for any plan text and never raises on a malformed plan (it returns `None` values instead).
  - Execution state: pending

- [ ] E-04 In `review_tier.py`, add `parse_tier_marker(reply_text: str) -> str | None`: the last non-empty line of the reply, after stripping surrounding whitespace and ignoring a trailing code-fence line, must equal exactly `AW-TIER: simple`, `AW-TIER: standard`, or `AW-TIER: complex` (case-sensitive), and the function returns the tier, else `None` (spec Section 6 row T and Section 8.1 rules 1 and 2, applied to this marker). Add `parse_tier_answers(review_text: str) -> dict[int, str] | None`: find the last `## Round <n>` section, then its `### Step T` subsection, and return the answers to questions 1 to 5, read as lines starting with `1.` to `5.` (or `Q1:` to `Q5:`); return `None` when the subsection is absent. Add `tier_answers_complete(answers) -> bool` (all five present and non-empty), which Order 04's postcondition for check T calls.
  - Depends on: none
  - Expected outcome: the three functions exist and are pure.
  - Execution state: pending

### Task group 3: run state and analytics

- [ ] E-05 In `review_tier.py`, add `record_review_tier(attempt: MutableMapping, *, tier: str | None, source: str, answers: Mapping[int, str] | None, facts: Mapping | None) -> None`, which writes `attempt["review_tier"]` (the tier or `None`), `attempt["review_tier_source"]` (`"agent"` for a marker-chosen tier, `"orchestrator"` for the fixed profile, `"raised"` when the agent raised it later per spec Section 5.3), `attempt["review_tier_answers"]` (a dict with string keys `"1"` to `"5"`, JSON-safe), and `attempt["review_tier_facts"]`. It never changes the tier it is given: spec MD-1 says the runner forces no tier. Order 04 calls it; this plan only provides it.
  - Depends on: E-03, E-04
  - Expected outcome: after a call, the attempt dict carries the four keys and `json.dumps(attempt)` succeeds.
  - Execution state: pending

- [ ] E-06 Carry the tier into the attempt grain: in `run_dashboard.collect_rows` add a `review_tier` row value (the attempt's `review_tier` when a non-empty string, `""` when the key is missing), add `review_tier` to `COLUMNS` and `ATTEMPT_FACT_FIELDS`, and bump `ATTEMPT_FACTS_SCHEMA_VERSION` by one; in `run_analytics_attempts` add `review_tier` to `ATTEMPT_FILTER_FIELDS` and `ATTEMPT_GROUP_FIELDS`. This follows the `readiness` addition of plan `avg8qv` exactly. In `docs/run-analytics.md` section "Review cost: per-attempt analysis", add the row `| Attempts by review tier | aw runs query attempts --filter action=review --group-by review_tier --metric cost,steps |` and remove nothing from "What is not recorded yet" (review steps stay listed until Order 04).
  - Depends on: E-05
  - Expected outcome: `aw runs query attempts --group-by review_tier` is accepted, and `aw runs query schema` lists `review_tier`.
  - Execution state: pending

### Task group 4: tests and commit

- [ ] E-07 Add `tests/test_review_tier.py`, marked `core`, covering: (a) `ipd_lint.lint_text` on a minimal conformant plan with `- Review-Depth: standard` reports no `IPD-M103`/`IPD-M104`, and with `huge` reports `IPD-M104`; (b) `ipd_lifecycle.frozen_region_digest` is equal for the same plan with and without the field; (c) `tier_facts` on three fixture plans (one naming a `.spec.md`, one with 19 E-items, one with no `- Scope-Paths:`) returns the expected values; (d) `parse_tier_marker` accepts each valid marker, accepts it before a trailing fence line, and returns `None` for `aw-tier: simple`, a marker that is not on the last line, and an unknown tier; (e) `parse_tier_answers` on a review text with two rounds reads the last round only and `tier_answers_complete` is false when answer 4 is missing; (f) `record_review_tier` writes the four keys and the result survives `json.dumps`; (g) the attempt-grain round trip: a fixture run whose attempt carries `review_tier: "simple"`, analyzed by the real `aw runs analyze` leaf, answers `run_query("attempts", group_by="review_tier", ...)` with a `simple` row (reuse the fixture helpers of `tests/test_run_analytics_review_cost.py`).
  - Depends on: E-01, E-03, E-04, E-05, E-06
  - Expected outcome: a passing core test module that calls the real functions and CLI leaf.
  - Execution state: pending

- [ ] E-08 Add one `CHANGELOG.md` entry (plans may record `- Review-Depth:`; review attempts can record their tier, queryable by `--group-by review_tier`), no em or en dashes. Run `python3 -m pytest -o addopts="" -n auto tests/test_review_tier.py tests/test_ipd_lint.py tests/test_ipd_schema.py tests/test_run_analytics_review_cost.py tests/test_run_dashboard.py`, the bare core gate `python3 -m pytest`, and `aw check`; commit through `aw commit gv3smb -- <each changed path>`. Never push.
  - Depends on: E-02, E-07
  - Expected outcome: both pytest runs pass; `aw check` reports no error and no warning this plan introduced; one path-scoped commit.
  - Execution state: pending

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
- Storage under metadata spec `4sd62s` (event logs): spec `k3yx72` Section 12 requires the `4sd62s` migration to carry `Review-Depth` like any other field if this lands first; nothing is owed here.

## Scope check

- Over-scope: none.
- Under-scope: none. Spec Sections 4.1 item 4, 5.2 (recording), 7.2 (field) and 12 (field naming) are covered.

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

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` hunk of `agent_workflows/ipd_schema.py` adding `META_REVIEW_DEPTH`, `REVIEW_DEPTH_VALUES`, the `META_RECOGNIZED` entry, and the enum check.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` of the structure-and-linting spec Section 4.4 paragraph and its history line, and of `.aw/records/plans/README.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -c` output calling `review_tier.tier_facts` on this plan file's own text, showing all seven keys and their values.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_tier.py -k "marker or answers"` with every selected test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_tier.py -k record` with every selected test PASSED, and quote the assertion that the recorded tier equals the tier passed in.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `git diff` hunks in `run_dashboard.py` and `run_analytics_attempts.py`, and `aw runs query schema --json` output filtered to show `review_tier` in both attempt-grain field lists.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_tier.py` with every test PASSED and none skipped.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the summary lines of the E-08 named pytest run and the bare `python3 -m pytest`, the `aw check` summary compared with the baseline taken before E-01, and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit gv3smb -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
