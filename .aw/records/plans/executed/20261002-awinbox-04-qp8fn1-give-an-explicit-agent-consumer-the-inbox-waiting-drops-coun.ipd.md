# IPD: Give an explicit --agent consumer the inbox waiting-drops count as a scalar Evidence key, on the measurement that route (c)'s invisibility cost is false and route (b)'s findings inflation is still live

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `xqem10` carries OQ-02 of executed plan `olmvgw`: the `.aw/inbox/` waiting-drops nudge reaches the HUMAN board (including every agent reading it through a pipe) but reaches NO explicit `--agent`/`--json` consumer. The item frames it as a maintainer judgement because it costs all three of its candidate routes against a shared output contract. I RE-DROVE ALL THREE COSTINGS IN THIS LANE AT HEAD `2b6fcd437` rather than inheriting them, and the item's own evidence DECIDES the question once one of its three cost claims is corrected.
  THE ITEM'S PRECONDITION IS SATISFIED AND ITS DEFECT IS REAL (F-01, F-02). Plan `olmvgw` is in `.aw/records/plans/executed/`, `attention.inbox_waiting` exists, and a real board over a temp repo with two drops prints `TODO: 2 files waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.`. Driving the SAME repo through `--agent` with two drops and then with zero produced BYTE-IDENTICAL records (`findings: 9`, `evidence: ["attention"]` in both), so the count is provably absent from the explicit machine surface. `--format json` and `--json` are the same 6178-byte `render_json` payload and carry no inbox key either.
  ROUTE (b)'s BLOCKER IS STILL LIVE, SO THE ITEM'S "WHAT WOULD UNBLOCK" HOPE HAS NOT MATERIALIZED, AND THAT MATTERS BECAUSE IT IS THE REASON THE ITEM SAID TO WAIT (F-03, F-04). `result_types.CommandResult.to_agent_record` still derives `findings` as `len(self.diagnostics) if self.diagnostics else self.data.get("findings", 0)` with NO severity filter; I constructed a clean `CommandResult` carrying ONE `severity="warning"` `Diagnostic` and got `outcome: clean, exit: 0, findings: 1` against `findings: 0` without it, reproducing the item's measurement exactly. The item says route (b) becomes cheap "if either [`zosk0a` or `xqm16x`] is fixed such that a warning no longer inflates findings". NEITHER DOES, and this is the item's one factual error rather than a matter of timing: `zosk0a` is `done`, its carrier `tzjtg4` is `executed`, and its declared `Scope-Paths` are `agent_workflows/cli.py, tests/test_check_severity_tally.py`; `xqm16x` is `graduated` to approved plan `nwcf8j`, whose `Scope-Paths` are `agent_workflows/doctor.py, agent_workflows/attention.py, tests/test_severity_truth_surfaces.py`. NEITHER declares `agent_workflows/result_types.py`, and NO pending plan in the tree does. Both items fix a DIFFERENT tally (`aw check`'s human `errors`/`warnings`/`info` Evidence row, which `tzjtg4` landed as a severity-keyed count in `cli.py`); the `aw.agent/v1` `findings` integer is untouched by either. So the sequencing advice the item gives is correct in principle and its trigger has not fired, which is precisely why route (b) must be refused on today's measurement rather than waited on.
  THE DECIDING CORRECTION: ROUTE (c)'s COST CLAIM IS FALSE, AND IT IS FALSE IN THE DIRECTION THAT SETTLES THE QUESTION (F-05, F-06). The item rejects route (c) because "the compact agent record sanitizes evidence to the bare key name, so the number is visible only under `--verbose`, making it nearly as invisible as (a)". That is true for a DICT value and FALSE for a SCALAR one. `agent_schema.sanitize_evidence_item` returns `f"{key}:{val}"` when `val` is an `(int, float, bool)` and falls back to the bare `key` only for a non-scalar; I built a `CommandResult` with `Evidence(key="inbox-waiting", value=2)` beside the existing dict-valued `attention` key and the COMPACT record read `evidence: ["attention", "inbox-waiting:2"]` with `findings: 0`. This is not a novel trick: `aw layout --agent` ships exactly this shape today (`evidence: ["record_classes:11", "logical_roots:4"]` from two scalar `Evidence` values in `cli._run_layout`), and `docs/cli-output-contract.md` publishes the form in its own compact example (`"evidence":["ipd-lint:author"]`). So route (c) delivers the number in the DEFAULT compact record, at zero cost to `findings`, following a shipped and documented precedent.
  WHY THIS IS AUTHORED RATHER THAN RETURNED TO THE MAINTAINER. The item assigns itself to the maintainer on the ground that it is "a judgement about who the nudge is for and about what findings promises, not a technical choice". The second half is the half that was load-bearing, and it is now answered by measurement rather than by taste: route (c) does not touch `findings`, so the contract question evaporates, and the remaining choice is between shipping a number at no contract cost and withholding it for no stated benefit. I resolve it as route (c) and record the reasoning for a reviewer to overturn, because `AGENTS.md` instructs an agent to resolve a blocking question from repository evidence and to ask only where the repo genuinely cannot answer. The genuinely maintainer-owned residue (should the VERSIONED `--format json` payload gain the key, which is a `schema_version` bump) is NOT taken here and is carried as OQ-01.
  WHY `chore` RATHER THAN THE ITEM'S `followup`, AND WHY NO RELEASE GATE. The item is `- Work-Kind: followup` carrying no `- Blocks-Release:`, and I inherit that absence rather than inventing a gate. I also do NOT promote this to `bug` on the repository's perceptibility test in `AGENTS.md`: nothing a user runs returns a wrong answer and nobody waits longer, because the human board already carries the line. The cost is a capability an explicit `--agent` consumer lacks, which is a missing feature and not a defect.
- Scope: IN, four things. (1) Emit ONE additive scalar `Evidence(key="inbox-waiting", value=<int>)` on `attention.run`'s explicit agent/json branch (the `if ctx.is_agent:` arm that already builds the `attention` Evidence), so the DEFAULT compact record carries `inbox-waiting:<n>` and the `--verbose` record carries the full dict, reusing the already-shipped `attention.inbox_waiting` and adding no second derivation. (2) Emit it ONLY when the count is NONZERO, matching the human footer's silent-when-empty rule, so a drained inbox's record is byte-identical to today's. (3) Prove `findings`, `outcome`, `exit`, and `diagnostics` are byte-unchanged by the addition, which is the whole reason route (c) is chosen over route (b). (4) Pin all of it behaviorally in `tests/test_attention.py` beside the existing `InboxWaitingCountTests`/`InboxFooterNudgeTests` classes that `olmvgw` added.
  OUT, each for a stated reason. ROUTE (b), A WARNING `Diagnostic`, is REFUSED rather than deferred, on F-03's live reproduction: it would inflate a clean repo's `findings` from 0 to 1. FIXING THE SEVERITY-BLIND `findings` TALLY in `result_types.to_agent_record` is a repo-wide `aw.agent/v1` contract change touching every verb, measured in F-04 as owned by NO pending plan, and is filed as a carrier rather than absorbed into a one-key addition. THE VERSIONED `--format json`/`--json` PAYLOAD gains nothing: `render_json` is a `schema_version: 4` consumer contract with a test asserting that value, so a new top-level key is a deliberate bump (OQ-01, carried). `attention.inbox_waiting` ITSELF is not modified: it shipped with `olmvgw` and its listing-only safety property is relied upon here, not revisited. THE `--check` AND `--check --agent` PATHS gain nothing, because a waiting local gitignored drop is not a repository defect and must never reach the exit code. THE HUMAN BOARD is not touched: its line already ships. `attention_contract.py` is NOT declared and a felt need to edit it means the count has leaked into classification.
- Scope-Paths: agent_workflows/attention.py, tests/test_attention.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: xqem10
- Set: awinbox
- Order: 4
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: qp8fn1

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: qp8fn1 verified (set awinbox, attempt 1).
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): status transition for the /plan-review record below

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: the gate's finalize instruction now carries conditional runner/executor ownership). Re-measured at HEAD `07bc746c7`: F-02 (identical `--agent` evidence `["attention"]` with 0 and 2 drops; board footer present), F-03 (one warning `Diagnostic` -> `findings: 1`, `outcome: clean`), F-04 (no pending plan's Scope-Paths declares `result_types.py`; `3ouico` open), F-05/F-06 (`sanitize_evidence_item` returns `key:val` for scalars; `layout --agent` emits `record_classes:11`), and the `--json` path is `render_json` at `schema_version: 4`. Review record `.aw/records/reviews/20261002-awinbox-04-qp8fn1-give-an-explicit-agent-consumer-the-inbox-waiting-drops-coun.review.md`.
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `xqem10`, inheriting its absence of a `- Blocks-Release:` gate rather than inventing one. EVERY measurement in `## Findings` was taken in this lane at HEAD `2b6fcd437`; none is transcribed from the item.
  THE ITEM'S PRECONDITION AND ITS DEFECT BOTH HOLD (F-01, F-02). `olmvgw` is executed, the footer line renders on a real board, and the explicit `--agent` record is byte-identical with two drops and with zero.
  I CORRECTED ONE FACTUAL ERROR AND ONE STALE HOPE IN THE ITEM, AND BETWEEN THEM THEY DECIDE THE QUESTION. The error is route (c)'s cost: the item says the compact record "sanitizes evidence to the bare key name", which is true only for a DICT value. `sanitize_evidence_item` returns `key:value` for an `(int, float, bool)`, so a SCALAR count is visible in the DEFAULT record (F-05), and `aw layout --agent` already ships exactly that shape while `docs/cli-output-contract.md` publishes it (F-06). The stale hope is the "what would unblock route (b)" paragraph: `zosk0a` is `done` and `xqm16x` is `graduated`, but NEITHER their carriers nor ANY pending plan declares `agent_workflows/result_types.py`, and both fix a DIFFERENT tally in `cli.py`/`doctor.py`, so the `aw.agent/v1` `findings` integer is exactly as severity-blind as when the item was filed (F-03, F-04).
  SO I RESOLVED THE QUESTION RATHER THAN RETURNING IT. The item's stated reason for maintainer ownership is "what `findings` promises", and route (c) does not touch `findings` at all, which removes the contract question the ownership rested on. The genuinely maintainer-owned residue is the VERSIONED json payload's `schema_version` bump, which this plan does NOT take and which is carried as a non-blocking OQ-01 with a named carrier.
  NO CARRIER IS LEFT UNFILED. The severity-blind `findings` tally is the one obligation this plan declines that did not already have a home, so it was FILED AT AUTHORING as backlog `3ouico` (`chore`, no release gate, carrying the F-03 reproduction and the F-04 measurement that it is a duplicate of NEITHER `zosk0a` NOR `xqm16x`) rather than left in prose; `check.ipd-uncarried-obligation` is error-severity for a post-cutover plan and would have refused this one. OQ-01's residue stays with `xqem10`, the item this plan graduates from.
  BASELINE RE-DERIVED, NOT TRANSCRIBED: bare `python3 -m pytest` gave `3 failed, 4624 passed, 2 skipped, 3 warnings in 112.25s` with 232 deselected. All three failures are pre-existing, outside both declared paths, and named in F-07; the bar is an UNCHANGED failing node-id set, never a green run.

## Goal

Let an agent that explicitly asks for machine output (`aw attention --agent`) learn that raw drops are waiting in `.aw/inbox/`, by adding one additive scalar Evidence key that is visible in the default compact record and provably cannot move `findings`, `outcome`, or `exit`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: confirm the premise before changing anything

- [x] E-01 RE-MEASURE THE FOUR FACTS THIS PLAN TURNS ON AT THE EXECUTING HEAD, AND STOP IF ANY HAS MOVED.
  DO THIS FIRST. Three of the four are LIVE properties that other approved lanes are editing (`nwcf8j` declares `agent_workflows/attention.py`, and F-08 lists further approved plans declaring it), so a plan authored on today's tree can be reasoning about code that has since changed.
  THE FOUR, each with the exact check. (1) `attention.inbox_waiting` EXISTS and the human footer line renders: `hasattr(agent_workflows.attention, "inbox_waiting")` is True and a real board over a temp repo with two drops prints the `waiting in `.aw/inbox/`` line. (2) THE EXPLICIT AGENT RECORD STILL OMITS THE COUNT: the same temp repo driven through `--agent` with two drops and with zero yields records whose `evidence` lists are IDENTICAL and contain no inbox key. (3) ROUTE (b) IS STILL BLOCKED: a clean `CommandResult` carrying one `severity="warning"` `Diagnostic` still reports `findings: 1`. (4) ROUTE (c) STILL WORKS: `agent_schema.sanitize_evidence_item` still returns `key:value` for an `int`, demonstrated by `python3 -m agent_workflows layout --agent` still emitting `record_classes:<n>`.
  STOP AND REPORT IF (3) IS FIXED, because route (b) would then be the cheaper answer following a precedent already inside `attention.run`, and this plan's central reasoning would be obsolete rather than merely tunable. STOP AND REPORT IF (4) IS BROKEN, because the chosen route would no longer deliver a visible number and the plan would be shipping the invisibility it exists to fix. STOP AND REPORT IF (2) IS ALREADY FIXED, since the feature would already exist and this plan is moot.
  - Depends on: none
  - Expected outcome: all four facts re-measured at the executing HEAD with commands and output pasted, each either CONFIRMED or reported as moved; execution proceeds only if (1) and (2) confirm the defect is live and (3) and (4) confirm the route choice still holds.
  - Execution state: performed

### Task group 2: the one additive key

- [x] E-02 EMIT ONE ADDITIVE SCALAR `Evidence(key="inbox-waiting", value=<int>)` ON `attention.run`'s EXPLICIT AGENT BRANCH, ONLY WHEN THE COUNT IS NONZERO.
  THE SITE IS THE `if ctx.is_agent:` ARM that already builds `evidence = [Evidence(key="attention", value={"items": ..., "drift": ...}, status=status)]`. Append to that list; do not construct a second `CommandResult` and do not touch the `if check:` arm above it, which has its own `attention` Evidence and must stay silent (a waiting drop is not a `--check` condition).
  USE A SCALAR `int` VALUE, AND THAT IS THE WHOLE DESIGN RATHER THAN A STYLE CHOICE. `agent_schema.sanitize_evidence_item` renders an `(int, float, bool)` value as `f"{key}:{val}"` and degrades a DICT to the bare key name, so a dict here would reproduce exactly the invisibility the backlog item wrongly attributed to this route (F-05). Do NOT "improve" it into `value={"waiting": n}`: that silently reverts the fix while leaving the code looking correct, and the `--verbose` surface is not the one this plan is about.
  REUSE `attention.inbox_waiting`, NEVER RE-DERIVE THE COUNT. It shipped with `olmvgw` and carries the listing-only safety property (it lists with `os.scandir` and opens no file, because `selectors._ID_RE` would harvest a body-quoted `- Id:` from unvetted text as an identity claim). A second derivation could disagree with the human footer's number, and only one of them would be right at a time. Call the existing function.
  EMIT ONLY WHEN NONZERO, matching the footer's silent-when-empty rule. The reason is a contract one rather than aesthetic: a drained inbox's record must be BYTE-IDENTICAL to today's, so no existing consumer sees a new key appear on a repository where nothing is waiting. A zero-valued key would also train a reader to ignore it.
  NEVER CONSTRUCT A `Diagnostic` FOR THIS, which is route (b) and is refused on F-03. The exit code is owned solely by `core.drift_exit_code(drift)`, and a diagnostic would additionally inflate `findings` on a clean repo.
  SET NO `status=` THAT IMPLIES A FINDING. The sibling `attention` Evidence carries `status=status` (which is `clean` or `findings` from the drift set); this key describes a local advisory condition and must not claim a finding status of its own. Use the dataclass default (`verified`), and say in a comment that the value is an observation rather than a verdict.
  - Depends on: E-01
  - Expected outcome: `aw attention --agent` on a repo with N>0 waiting drops emits `inbox-waiting:N` in its compact `evidence` list; the same repo drained emits a record byte-identical to today's; the count comes from `attention.inbox_waiting` with no second derivation; no `Diagnostic` is constructed; the `if check:` arm is unmodified.
  - Execution state: performed

- [x] E-03 PROVE THE ADDITION CANNOT MOVE `findings`, `outcome`, `exit`, OR `diagnostics`, WHICH IS THE ENTIRE REASON THIS ROUTE WAS CHOSEN OVER ROUTE (b).
  THIS IS NOT A RESTATEMENT OF E-02; IT IS THE CLAIM THAT JUSTIFIES THE DESIGN. `to_agent_record` derives `findings` from `len(self.diagnostics)` and falls back to `self.data.get("findings", 0)`, so an Evidence entry cannot reach it by construction. Demonstrate that rather than asserting it: capture the full record for a repo with waiting drops and the same repo drained, and show the two differ in the `evidence` list and in NOTHING else.
  INCLUDE THE SCHEMA VALIDATOR IN THE PROOF. `agent_schema.validate_agent_record` enforces exit/outcome parity and refuses greenwashing, so a record carrying the new key must still validate; a route that produced `outcome: clean` with a negative pairing would be rejected at render time. Run the validator (or the real CLI, which renders through it) rather than only inspecting a hand-built dataclass.
  COVER BOTH VERBOSITY LEVELS, because they take different branches of `to_agent_record`'s evidence handling: the default compact path calls `sanitize_evidence_item` (yielding `inbox-waiting:N`) and `--verbose` emits the full dict. Both must carry the number, and neither may alter `findings`.
  - Depends on: E-02
  - Expected outcome: paired full `--agent` records (drops present vs drained) differing ONLY in `evidence`, with `findings`, `outcome`, `exit`, `verified`, `complete`, and `diagnostics` identical; the record validating under `agent_schema.validate_agent_record`; the count present under both default and `--verbose`.
  - Execution state: performed

### Task group 3: pin it behaviorally

- [x] E-04 PIN THE BEHAVIOR IN `tests/test_attention.py` BESIDE THE CLASSES `olmvgw` ALREADY ADDED.
  SITE IT WITH ITS TWINS: `InboxWaitingCountTests` and `InboxFooterNudgeTests` already exist in this file and build temp repos via the file's `_mk_repo` helper, driving the CLI with an `argparse.Namespace` plus `attention.run` under `redirect_stdout`. Reuse that pattern; do not found a new test module for one key.
  BUILD EVERY CASE IN A TEMPORARY REPO AND NEVER READ THE REAL `.aw/inbox/`. It is gitignored and per-checkout, so a test pinned to it passes on one machine and fails on another. `olmvgw`'s V-05 evidence records a grep proving its own tests avoid it; hold the same bar.
  THE REQUIRED CASES. (1) N>0 drops: the compact `--agent` record's `evidence` list CONTAINS `inbox-waiting:N` with the right N. (2) DRAINED (bookkeeping-only `README.md` plus `.gitkeep`, which `inbox_waiting` excludes): the key is ABSENT. (3) THE CONTRACT CASE, and the one that makes this plan's reasoning a tested invariant rather than a comment: `findings` is EQUAL between the drops-present and drained records, which is the assertion that would fail had route (b) been taken. (4) `--verbose` carries the number too. (5) THE `--check --agent` ARM IS UNAFFECTED: its record carries no inbox key, pinning that a local gitignored drop never reaches the validity surface.
  ASSERT ON OUTCOMES, NEVER ON CODE STRUCTURE. Do not read `attention.py` with `inspect`, `ast`, regex, or substring search; do not assert on caller counts or symbol censuses; do not assert that any particular literal appears in the implementation (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). Parse the emitted JSONL record and assert on its fields.
  `tests/test_attention_contract.py` MUST PASS UNMODIFIED. It owns enum totality and the class maps; if it needs editing, the count has leaked into classification and the design is wrong. Stop and report rather than editing it.
  - Depends on: E-03
  - Expected outcome: new cases covering all five listed conditions pass in temporary repos; `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_attention_blind_spot.py -o addopts=""` passes with a count raised by exactly the number of tests added (authoring measured `106 passed`); `tests/test_attention_contract.py` unmodified; no test reads the real `.aw/inbox/`; the bare suite's failing node-id set unchanged against E-01's re-derived baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A SCALAR `Evidence` VALUE SURVIVES THE COMPACT AGENT RECORD; A DICT DOES NOT. `agent_schema.sanitize_evidence_item` returns `f"{key}:{val}"` for an `(int, float, bool)` value and the bare `key` otherwise. This single fact is why this plan chooses route (c) and why the backlog item rejected it.
- THE SHIPPED PRECEDENT IS `aw layout --agent`. `cli._run_layout` builds two scalar `Evidence` values (`record_classes`, `logical_roots`) and the record reads `evidence: ["record_classes:11", "logical_roots:4"]`. `docs/cli-output-contract.md` also publishes the form in its own compact example (`"evidence":["ipd-lint:author"]`).
- `findings` IS SEVERITY-BLIND AND IS DERIVED FROM DIAGNOSTICS ALONE. `result_types.CommandResult.to_agent_record` computes `len(self.diagnostics) if self.diagnostics else self.data.get("findings", 0)`. An `Evidence` entry cannot reach it, which is the structural reason route (c) is free and route (b) is not.
- `attention.run` HAS THREE MACHINE EXITS AND THEY ARE DISTINCT. The `if check:` arm emits its own `CommandResult` and returns early; the `if ctx.is_agent:` arm emits the record this plan edits; and `if fmt == "json" or ctx.is_json:` writes `render_json`'s versioned object. Measured: `--json` and `--format json` produce the SAME 6178-byte payload, so they are one surface and not two.
- THE ADVISORY-NEVER-GATES RULE IS ALREADY HOUSE LAW IN THIS FUNCTION. The exit code is owned solely by `core.drift_exit_code(drift)`, and the `order-notices`, `release-gate-warnings`, and (per `olmvgw`) inbox-footer sections each state that they cannot affect it.
- THE ORDER-NOTICE PRECEDENT IS REAL BUT IS ROUTE (b). `attention.run` already emits `order_notices` as `severity="warning"` diagnostics, commented "an ordering notice must reach an AGENT too, not only the human board". It is cited here as the thing this plan deliberately does NOT copy, because F-03 measures its cost.
- `inbox_waiting` LISTS AND NEVER OPENS, BY DESIGN. Its docstring records that `selectors._ID_RE` is position-unanchored, so a body-quoted `- Id:` in unvetted text would be harvested as an identity claim; it uses `os.scandir` and excludes `README.md`/`.gitkeep` because `.aw/inbox/README.md` is TRACKED.
- THE JSON PAYLOAD IS A VERSIONED CONTRACT AT `schema_version: 4` with a test asserting that value, so adding a top-level key there is a deliberate bump (OQ-01) rather than an additive free move.
- `aw.agent/v1` IS ADDITIVE-STABLE BY ITS OWN PUBLISHED RULE. `docs/cli-agent-protocol.md`: "Additive, optional fields within `aw.agent/v1` are backward compatible... Pin your parser to the `schema` string and tolerate unknown fields." A new Evidence ENTRY is not even a new field.
- NO TEST PINS `attention`'s EVIDENCE LIST. A grep for evidence assertions across `tests/` finds `test_check_severity_tally.py` (the `rules` key), `test_json_surface_leak_posture.py` (redaction posture on `evidence[0]`) and others, none of them driving `attention`, so an appended key breaks no existing pin.
- TESTS MUST ASSERT OUTCOMES, NOT CODE STRUCTURE (`AGENTS.md`; GUIDING_PRINCIPLES P16): no `inspect`/`ast`/regex reads of production source, no caller counts or symbol censuses, no pinning docstrings or comment banners.
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the `not slow and not livecorpus` marker filter; do not add `-n0`, a second `-q`, or `-p no:randomly`. Clear defaults explicitly with `-o addopts=""` only where per-test counts are needed.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured in this lane worktree at HEAD `2b6fcd437` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-01 | N/A | `.aw/records/plans/executed/20260930-awinbox-03-olmvgw-*.ipd.md`, `attention.inbox_waiting` | THE ITEM'S PRECONDITION IS SATISFIED, so there is a count to surface. `olmvgw` is in `executed/` with `- Status: executed`, `attention.inbox_waiting` exists, and a real board over a temp repo holding two drops printed `TODO: 2 files waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.`. | `ls`; `python3 -m agent_workflows attention --dir <tmp> --no-color` |
| F-02 | MED | `attention.run`'s `if ctx.is_agent:` arm; `render_json` | THE DEFECT THE ITEM REPORTS IS REAL AND THE COUNT IS ABSENT FROM BOTH EXPLICIT MACHINE SURFACES. The SAME temp repo driven through `--agent` with two drops and then with zero produced records whose `evidence` was `["attention"]` and whose `findings` was `9` in BOTH cases, byte-identical. The versioned payload carries no inbox key either: its top-level keys are `['items', 'mapping_version', 'schema_version', 'stranded_lanes', 'valid', 'violations']` at `schema_version: 4`. | drove `--agent` twice and diffed; `--format json` key dump |
| F-03 | HIGH | `result_types.CommandResult.to_agent_record` | ROUTE (b) IS STILL BLOCKED, REPRODUCING THE ITEM'S MEASUREMENT EXACTLY. `findings` is derived as `len(self.diagnostics) if self.diagnostics else self.data.get("findings", 0)` with NO severity filter. A clean `CommandResult` (`status='clean'`, `exit_code=0`) carrying ONE `severity="warning"` `Diagnostic` produced `outcome: clean, exit: 0, findings: 1`; without it, `findings: 0`. So a warning diagnostic still puts a phantom finding on a healthy repo. | constructed both records and printed them |
| F-04 | HIGH | `zosk0a`, `xqm16x`, `tzjtg4`, `nwcf8j`, `.aw/records/plans/pending/` | THE ITEM'S "WHAT WOULD UNBLOCK ROUTE (b)" IS FACTUALLY WRONG, AND THIS IS WHAT STOPS THIS PLAN FROM SIMPLY WAITING. The item says route (b) becomes cheap if `zosk0a` or `xqm16x` is fixed "such that a warning no longer inflates findings". `zosk0a` is `done` (carrier `tzjtg4`, `executed`, `Scope-Paths: agent_workflows/cli.py, tests/test_check_severity_tally.py`) and `xqm16x` is `graduated` (carrier `nwcf8j`, `approved`, `Scope-Paths: agent_workflows/doctor.py, agent_workflows/attention.py, tests/test_severity_truth_surfaces.py`). NEITHER declares `agent_workflows/result_types.py`, and a scan of every pending plan's `- Scope-Paths:` finds NO plan that does. Both items fix a DIFFERENT tally: `aw check`'s human Evidence row, which `tzjtg4` landed as a severity-keyed `{"errors": .., "warnings": .., "info": ..}` count in `cli.py` (verified: `aw check plans --agent --verbose` shows the `rules` key carrying that dict). The `aw.agent/v1` `findings` INTEGER is untouched by either, exactly as F-03 measures. | `- Status:`/`- Scope-Paths:` reads on all four artifacts; tree-wide `Scope-Paths` grep for `result_types.py`; `check plans --agent --verbose` |
| F-05 | HIGH | `agent_schema.sanitize_evidence_item` | THE ITEM'S ROUTE (c) COST CLAIM IS FALSE, AND ITS FALSITY DECIDES THE QUESTION. The item says the compact record "sanitizes evidence to the bare key name" so the number is "visible only under `--verbose`". The function returns `f"{key}:{val}"` when `val` is an `(int, float, bool)` and falls back to the bare `key` only for a non-scalar. Measured: a `CommandResult` carrying `Evidence(key='attention', value={'items':1,'drift':0})` AND `Evidence(key='inbox-waiting', value=2)` produced the COMPACT record `evidence: ['attention', 'inbox-waiting:2']` with `findings: 0`. So the dict-valued key degrades (as the item describes) and the scalar one does NOT. | read the function; built the record and printed its compact form |
| F-06 | MED | `cli._run_layout`; `docs/cli-output-contract.md` | THE SCALAR-EVIDENCE SHAPE IS ALREADY SHIPPED AND ALREADY PUBLISHED, so this plan follows a precedent rather than inventing a convention. `aw layout --agent` emits `evidence: ["record_classes:11","logical_roots:4"]` from two scalar `Evidence` values built in `cli._run_layout`. `docs/cli-output-contract.md` publishes the same form in its own compact example (`"evidence":["ipd-lint:author"]`) and states the compact-defaults rule ("check names in evidence receipts ... rather than verbose text paragraphs"). `docs/cli-agent-protocol.md` additionally guarantees additive compatibility within `aw.agent/v1`. | ran `layout --agent`; read `_run_layout`; read both docs |
| F-07 | N/A | full bare suite | BASELINE, AND IT IS NOT GREEN, SO ZERO FAILURES IS NOT AN ACHIEVABLE BAR. Bare `python3 -m pytest` gave `3 failed, 4624 passed, 2 skipped, 3 warnings in 112.25s` with 232 deselected. The three are `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, and `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`. All three are outside both declared paths and are another party's; do NOT fix them. The four attention suites are GREEN at `106 passed`. Re-derive your own numbers and compare failing NODE IDS, never totals. | bare `python3 -m pytest`; targeted four-suite run with `-o addopts=""` |
| F-08 | LOW | sibling pending plans | APPROVED SIBLINGS DECLARE THIS PLAN'S PATHS AND NONE TOUCHES THE AGENT EVIDENCE BLOCK, recorded so a surprising diff is interpretable rather than alarming. `nwcf8j` (`approved`) declares `agent_workflows/attention.py` and edits the `severity="error"` hardcode on attention's diagnostics, which is the SAME `if ctx.is_agent:` arm this plan appends Evidence to; it changes `diagnostics`, this plan changes `evidence`, so they are adjacent but not conflicting. `r61br4` (`approved`) declares both of this plan's paths. The runner isolates each item in its own worktree and revalidates on merge, so no dependency edge is declared or needed. NOTE for the executor: if `nwcf8j` has landed first, the diagnostics construction nearby will look different from this plan's quotations, and that is expected rather than a sign the plan is stale. | `- Scope-Paths:` scan over `.aw/records/plans/pending/`; read `nwcf8j`'s E-03 |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the four live facts the plan turns on (the feature's presence, the defect's persistence, route (b)'s blocker, route (c)'s mechanism) and stops if any has moved, because approved siblings are editing the same module (F-08).
2. E-02 appends one additive scalar `Evidence(key="inbox-waiting", value=<int>)` to the existing evidence list on `attention.run`'s explicit agent branch, emitted only when nonzero, reusing `attention.inbox_waiting` (F-05, F-06).
3. E-03 proves the addition cannot move `findings`, `outcome`, `exit`, or `diagnostics`, and that the record still validates, which is the claim that justifies choosing route (c) over route (b) (F-03).
4. E-04 pins all five behaviors in `tests/test_attention.py` beside `olmvgw`'s classes, including the `findings`-equality assertion that would fail under route (b).

## Deferred / out of scope (with reason)

- **ROUTE (b), A WARNING `Diagnostic` ON THE AGENT PATH, IS REFUSED RATHER THAN DEFERRED.** F-03 reproduces its cost at this HEAD: one `severity="warning"` `Diagnostic` turns a clean repository's `findings: 0` into `findings: 1` while `outcome` stays `clean`, so a consumer reading `findings` as "problems found" sees a phantom finding. The item correctly identified this and incorrectly expected it to have been unblocked by now (F-04). Route (c) delivers the same visibility at zero contract cost, so route (b) is not postponed; it is the rejected alternative.
  - Carrier-Declined: No obligation is left outstanding. The audience need route (b) existed to serve is fully met by E-02's scalar Evidence key in the DEFAULT compact record, so nothing is half-done and no successor inherits a gap.
- **FIXING THE SEVERITY-BLIND `findings` TALLY IN `result_types.to_agent_record` IS GENUINELY OUT OF SCOPE.** It is a repo-wide `aw.agent/v1` contract shared by every verb, in a module this plan does not declare, and changing how `findings` is computed would move the number on every command at once. F-04 measures that it is owned by NO pending plan and that the two items the backlog item names (`zosk0a`, `xqm16x`) fix a DIFFERENT tally in `cli.py`/`doctor.py`, so the concern has no existing home and must be filed rather than cited.
  - Carrier: 3ouico
- **ADDING THE COUNT TO THE VERSIONED `--format json`/`--json` PAYLOAD IS NOT DONE HERE.** `render_json` is a `schema_version: 4` consumer contract with a test asserting that value, so a new top-level key is a deliberate bump requiring its own justification, which is out of proportion to one advisory count; and the number must never go inside `items`, where it would be classified as an artifact. This is the genuinely maintainer-owned residue of the item's question and is carried as OQ-01.
  - Carrier: xqem10
- **`attention.inbox_waiting` ITSELF IS NOT MODIFIED.** It shipped with `olmvgw` and its listing-only safety property (list with `os.scandir`, open nothing, exclude the tracked `README.md`) is RELIED UPON here rather than revisited. Re-deriving or "improving" the count is exactly what would let the agent surface disagree with the human board.
  - Carrier-Declined: No obligation is left outstanding. The function is correct for this use as shipped, so nothing about it is postponed.
- **THE `--check` AND `--check --agent` PATHS GAIN NOTHING.** A waiting drop is a local, gitignored condition no other machine can see, so it is not a repository defect and must never reach the validity surface or the exit code. E-04's fifth case pins that structurally rather than leaving it to taste.
  - Carrier-Declined: No obligation is left outstanding. This is a settled design property of the feature (established by `olmvgw` E-04 for the board and extended to the agent record by this plan's test), not deferred work.
- **THE HUMAN BOARD IS NOT TOUCHED.** Its footer line already ships from `olmvgw`, and this plan's whole subject is the surface the board does not reach.
  - Carrier-Declined: No obligation is left outstanding. The human audience is already served, so there is nothing to carry.
- **A TYPED INVENTORY OF INBOX CONTENTS (kinds, ages, topics) ON THE AGENT SURFACE IS OUT.** It would require reading the drops, which is the exact hazard `inbox_waiting` is built to avoid: `selectors._ID_RE` is position-unanchored, so a body-quoted `- Id:` in unvetted external text is harvested as an identity claim. A count is the whole feature.
  - Carrier-Declined: No obligation is left outstanding. The typed inventory is refused on a safety ground rather than postponed, since parsing a drop is the hazard the design exists to prevent.

## Scope check

- Over-scope: none. Both declared paths are modified: `agent_workflows/attention.py` by E-02 (one appended `Evidence` in the `if ctx.is_agent:` arm) and `tests/test_attention.py` by E-04. `agent_workflows/result_types.py` is NOT declared even though F-03 and F-05 read from it, and `agent_workflows/agent_schema.py` is NOT declared even though F-05 reads `sanitize_evidence_item`: both are measured, neither is edited. `agent_workflows/attention_contract.py` is deliberately NOT declared, and a felt need to touch it is the tripwire that the count has drifted into classification. No `.spec.md` path is declared (see `## Spec / documentation sync`).
- Cross-plan: F-08 records the survey rather than leaving it implicit, because this plan declares a heavily contended module. `nwcf8j` (`approved`) edits the diagnostics construction in the SAME `if ctx.is_agent:` arm this plan appends evidence to (it changes `severity`, this plan adds an `Evidence`), and `r61br4` (`approved`) declares both paths. Neither conflicts semantically; the runner isolates each item in its own worktree and revalidates on merge, so no `- Item-Dependencies:` edge is declared. E-01 instructs the executor to expect a different-looking neighborhood if `nwcf8j` landed first.
- Under-scope: stated rather than left as `none`. The VERSIONED `--format json`/`--json` payload gains nothing and its `schema_version` stays `4` (OQ-01). `--check` and `--check --agent` gain nothing, by design. The severity-blind `findings` tally is measured (F-03) and carried, not fixed. The human board is unchanged. So after this plan the count reaches the human board (including piped readers) AND the explicit `--agent` record, and remains absent from the versioned JSON object and every `--check` surface.

## Required tests / validation

All validation runs BARE (`python3 -m pytest`), per the execution contract: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the marker filter, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Where per-test counts are genuinely needed, clear the defaults explicitly with `-o addopts=""`.

RE-DERIVE YOUR OWN BASELINE AND DO NOT EXPECT A GREEN RUN. Authoring measured `3 failed, 4624 passed, 2 skipped, 3 warnings in 112.25s` with 232 deselected (F-07), the three failures being pre-existing and outside both declared paths. Run bare FIRST, record your number AND your failing node-id set, and state every delta against YOUR number, comparing failing NODE IDS rather than totals. Do NOT fix those tests.

1. TARGETED: `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_attention_blind_spot.py -o addopts=""` passes, with the new cases in the selected set and the count raised by exactly the number E-04 adds (authoring measured `106 passed`).
2. FULL BARE SUITE: `python3 -m pytest` shows an UNCHANGED failing node-id set against YOUR baseline and a passed count increased by exactly the number of tests E-04 adds.
3. THE CONTRACT TEST IS THE MOST IMPORTANT ONE: paste the output of the case asserting `findings` is EQUAL between the drops-present and drained `--agent` records. A passing count elsewhere is not evidence of it, and this is the assertion that would fail had route (b) been taken.
4. VISIBILITY IN THE DEFAULT RECORD: paste the compact `--agent` record for a repo with N>0 drops showing `inbox-waiting:N` in `evidence`, and the same repo drained showing the key ABSENT and the record otherwise byte-identical to the pre-change one.
5. BOTH VERBOSITY LEVELS: paste the `--agent` and `--agent --verbose` records for a populated repo, showing the number present in each (compact as `inbox-waiting:N`, verbose as the full dict).
6. SCHEMA VALIDITY: show the emitted record validating under `agent_schema.validate_agent_record` (or equivalently rendered by the real CLI, which validates at render time), proving the addition cannot produce a record the protocol rejects.
7. THE VERSIONED PAYLOAD IS UNTOUCHED: paste `render_json`'s top-level key list and `schema_version` with and without a waiting drop, IDENTICAL and still `4`.
8. `--check` UNAFFECTED: paste the `--check --agent` record with a waiting drop present, showing no inbox key, and the `aw attention` / `aw attention --check` exit codes for empty and populated inboxes, all equal.
9. `tests/test_attention_contract.py` passes UNMODIFIED: paste `git diff --stat` for it showing no change.
10. `aw sanitize --agent` exits 0, since this plan adds a rendered value to a surface that is pasted into shared contexts (the value is an integer count, so no path or identifier can reach it, which the run should confirm rather than assume).

## Spec / documentation sync

NO SPEC IS AMENDED, AND I VERIFIED THAT RATHER THAN ASSERTING IT. `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` binds the `--format json` payload as a versioned object (Section 8.3), the `--check`/`--agent` fail-closed exit contract (Section 8.1, F3/F3a/F4), the READ-ONLY guarantee ("Writes NOTHING to disk"), and byte-determinism (Section 8.5). This plan touches NONE of them: the versioned JSON payload is explicitly out of scope and keeps `schema_version: 4`; no `Drift` is constructed so no exit code moves; nothing is written; and the added value is a directory-entry count carrying no mtime or other time-derived value, so determinism holds. A case-insensitive grep for `evidence` over that spec finds no clause constraining the `aw.agent/v1` Evidence LIST (Section 8.3 governs the `location<TAB>rule<TAB>detail` violation record and the versioned json object), which is why the two existing advisory evidence/diagnostic additions in `attention.run` were made without amending it. No `.spec.md` path enters `- Scope-Paths:`.

NO USER-FACING DOCUMENT NEEDS EDITING, FOR A STATED REASON RATHER THAN BY OMISSION. `docs/cli-agent-protocol.md` already publishes the governing rule ("Additive, optional fields within `aw.agent/v1` are backward compatible... tolerate unknown fields"), and `docs/cli-output-contract.md` already documents the compact-evidence convention this plan follows, including the `key:value` example form. Neither enumerates per-verb evidence keys, so there is no table this addition falls out of date with. `CHANGELOG.md` is NOT declared because this is an additive machine-surface detail on an unreleased 2.0.0 line whose inbox-counter feature is not itself a shipped changelog entry; a reviewer who disagrees can require one, and the change is one line.

`AGENTS.md` already documents `.aw/inbox/` and is INSTALLED from `agent_workflows/engine.py`, so if the inbox contract ever needs restating the generator is the file to edit and never `AGENTS.md`. It does not need restating here: this plan changes no rule about what an inbox file is, and adds no new obligation on an agent reading one.

## Open questions

### OQ-01: Should the waiting count also appear in the VERSIONED `aw attention --format json` payload, at the cost of a `schema_version` bump?

- Blocking: no
- Status: deferred
- Owner: the maintainer (it is a versioned-consumer-contract change, not a mechanism question)
- Carrier: xqem10
- Resolution or deferral rationale: NOT BLOCKING, and deliberately not self-resolved, because unlike the `--agent` question this one cannot be answered by measurement alone. `render_json` emits `schema_version`, `mapping_version`, `valid`, `items`, `violations`, `stranded_lanes` at `schema_version: 4`, and `tests/test_attention.py` asserts that value, so a new top-level key is a DELIBERATE BUMP affecting every machine consumer of that payload, with a test update, and the number must never go inside `items` where it would be classified as an artifact. That is out of proportion to one advisory count, and executed plan `olmvgw`'s OQ-01 already resolved the same question NO on the same contract reasoning. WHY IT IS NOT MERELY CLOSED: the audience for the versioned payload is a stable programmatic consumer, and whether such a consumer should be able to see waiting drops is a product judgement about that contract's purpose, not a fact in the tree. THIS PLAN'S CHOICE NARROWS THE QUESTION USEFULLY rather than leaving it where `olmvgw` did: after E-02, an agent that wants the number has a supported route (`--agent`, where it is additive and free), so the only remaining reason to bump the versioned schema is a consumer that reads `--format json` exclusively and cannot switch. If no such consumer is named, the honest answer is to leave it. The carrier is `xqem10`, the item this plan graduates from, which remains the durable home for the residue of its own question.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste all four re-measurements with the exact command and its output. (1) `hasattr(agent_workflows.attention, "inbox_waiting")` printing True, plus a real board over a temp repo with two drops showing the `waiting in `.aw/inbox/`` line. (2) The `--agent` record for that SAME repo with two drops and with zero drops, both pasted in full, shown to have IDENTICAL `evidence` lists containing no inbox key (this is the defect; if the key is already present, STOP, the plan is moot). (3) A clean `CommandResult` carrying one `severity="warning"` `Diagnostic` printing `findings: 1`, and the same without it printing `findings: 0` (if the warning no longer inflates, STOP and report: route (b) is now cheaper and this plan's reasoning is obsolete). (4) `python3 -m agent_workflows layout --agent` showing `record_classes:<n>` in its `evidence` list, proving a scalar Evidence value still survives compaction (if it does not, STOP: the chosen route would ship the invisibility it exists to fix). Also paste the bare `python3 -m pytest` baseline summary line AND the full failing node-id list, which every later item compares against.
  - Observed evidence:
    All four facts re-measured at executing HEAD c8fb45659ddc8e17f360003bef965ff925200555:
    (1a) hasattr(agent_workflows.attention, "inbox_waiting"):
    $ python3 -c 'import agent_workflows.attention as a; print("hasattr inbox_waiting:", hasattr(a, "inbox_waiting"))'
    hasattr inbox_waiting: True
    (1b) Real board over temp repo with two drops:
    $ python3 -m agent_workflows attention --dir <tmp> --no-color
    ## active (1)
    - [research] .agents/docs/research/20260808-r-00-def456-r.survey.md (active)
    ## ready (2)
    - [specs] .agents/docs/specs/s.md (approved)
    - [plans] .agents/plans/pending/20260808-x-01-abc123-p.md (draft)
    3 artifacts shown
    TODO: 2 files waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one.

    (2) Pre-change --agent record on temp repo with two drops and with zero drops:
    2 drops:
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention"],"next":null}
    0 drops:
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention"],"next":null}
    Identical evidence lists: ['attention'] == ['attention'], no inbox key present (defect confirmed live).

    (3) Route (b) warning diagnostic inflation check:
    $ python3 -c 'from agent_workflows.result_types import CommandResult, Diagnostic; r1 = CommandResult(command="test", status="clean", exit_code=0, diagnostics=[Diagnostic(location="loc", rule="warn", detail="msg", severity="warning")]).to_agent_record(); r0 = CommandResult(command="test", status="clean", exit_code=0, diagnostics=[]).to_agent_record(); print("with warn:", r1["findings"], "clean:", r0["findings"])'
    with warn: 1 clean: 0
    (findings: 1 vs findings: 0; route (b) remains blocked).

    (4) Route (c) scalar evidence compaction check:
    $ python3 -m agent_workflows layout --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"layout","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["record_classes:11","logical_roots:4"],"next":null}
    (record_classes:11 present in evidence; scalar survives compaction).

    Bare python3 -m pytest baseline summary and failing node-id list:
    $ python3 -m pytest
    6430 passed, 2 skipped, 3 warnings in 403.63s (0:06:43) [258 deselected]
    Full failing node-id list: [] (none)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of the `if ctx.is_agent:` arm in context, showing the new `Evidence` APPENDED to the existing list beside the `attention` key, with a SCALAR `int` value (not a dict, which F-05 measures as invisible in the compact record) and no `status=` claiming a finding. Paste a grep or the diff itself proving no `Diagnostic` is constructed by the new code and that the `if check:` arm is unmodified. Paste a grep showing the count comes from a CALL to `attention.inbox_waiting` rather than a second `scandir`/`iterdir` derivation. Then paste three `--agent` records: N=1 showing `inbox-waiting:1`, N=2 showing `inbox-waiting:2`, and a bookkeeping-only (`README.md` plus `.gitkeep`) inbox showing the key ABSENT.
  - Observed evidence:
    (1) Diff of if ctx.is_agent: arm in agent_workflows/attention.py:
    ```diff
    @@ -4418,6 +4418,17 @@ def run(args) -> int:
                     status=status,
                 )
             ]
    +        waiting = inbox_waiting(repo_root)
    +        if waiting:
    +            # awinbox Order 04 (`qp8fn1`): emit the waiting-drops count as a scalar Evidence key
    +            # so it survives compact agent sanitization (f"{key}:{val}") with zero finding inflation.
    +            # Default status="verified" indicates an observation, not a finding/verdict.
    +            evidence.append(
    +                Evidence(
    +                    key="inbox-waiting",
    +                    value=waiting,
    +                )
    +            )
             res = CommandResult(
                 command="attention",
                 status=status,
    ```
    (2) No Diagnostic constructed in new code; `if check:` arm is unmodified (lines 4313-4357 untouched).
    (3) Count derives from call to `inbox_waiting(repo_root)`:
    `waiting = inbox_waiting(repo_root)`
    (4) Three --agent records from temporary test repositories:
    N=1:
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention","inbox-waiting:1"],"next":null}
    N=2:
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention","inbox-waiting:2"],"next":null}
    Bookkeeping-only (README.md + .gitkeep):
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention"],"next":null}
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the FULL `--agent` record for a populated inbox and for the same repo drained, side by side, and state explicitly which fields differ: `evidence` must differ and `findings`, `outcome`, `exit`, `verified`, `complete`, and `diagnostics` must be IDENTICAL. Paste the `--agent --verbose` record for the populated case showing the number present in the expanded evidence dict. Paste the result of validating the populated record through `agent_schema.validate_agent_record` (empty error list, or the real CLI rendering it, which validates at render time). Paste `render_json`'s top-level key list and `schema_version` for both states, IDENTICAL and still `4`, proving the versioned payload did not move.
  - Observed evidence:
    (1) Full --agent records for populated vs drained side by side:
    Populated:
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention","inbox-waiting:1"],"next":null}
    Drained:
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["attention"],"next":null}
    Field-by-field diff:
    - evidence: ['attention', 'inbox-waiting:1'] vs ['attention'] (DIFFERS as expected)
    - schema: 'aw.agent/v1' == 'aw.agent/v1' (IDENTICAL)
    - kind: 'result' == 'result' (IDENTICAL)
    - cmd: 'attention' == 'attention' (IDENTICAL)
    - outcome: 'clean' == 'clean' (IDENTICAL)
    - exit: 0 == 0 (IDENTICAL)
    - verified: True == True (IDENTICAL)
    - complete: True == True (IDENTICAL)
    - findings: 0 == 0 (IDENTICAL)
    - next: None == None (IDENTICAL)

    (2) --agent --verbose record for populated case:
    {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":[{"key":"attention","value":{"items":3,"drift":0},"status":"clean","detail":""},{"key":"inbox-waiting","value":1,"status":"verified","detail":""}],"next":null}
    Number present in evidence dict: {'key': 'inbox-waiting', 'value': 1, 'status': 'verified', 'detail': ''}.

    (3) agent_schema.validate_agent_record validation:
    validate_agent_record(obj_pop): [] (valid, 0 errors)
    validate_agent_record(obj_pop_verbose): [] (valid, 0 errors)

    (4) render_json comparison:
    Populated: keys=['schema_version', 'mapping_version', 'valid', 'items', 'violations', 'stranded_lanes'], schema_version=4
    Drained:   keys=['schema_version', 'mapping_version', 'valid', 'items', 'violations', 'stranded_lanes'], schema_version=4
    Key lists and schema_version are identical and unchanged at 4.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test names and the PASSING run of `python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_attention_blind_spot.py -o addopts=""` with its count stated against your own re-derived baseline (authoring measured `106 passed`). Paste IN FULL the test asserting `findings` EQUALITY between the drops-present and drained records, plus its passing output, since that is the assertion carrying this plan's central contract claim; then PROVE IT BITES by pasting the failure you get when the same case is evaluated against a deliberately route-(b) record (construct a `CommandResult` carrying one warning `Diagnostic` and show the equality assertion failing on it), demonstrating the test discriminates rather than passing vacuously. Paste the `--check --agent` case showing no inbox key. Paste a grep over the new tests showing NO reference to the real `.aw/inbox/` and no `inspect`/`ast`/regex read of `attention.py`. Paste `git diff --stat tests/test_attention_contract.py` showing it UNMODIFIED. Paste the FULL bare `python3 -m pytest` summary and state the delta against YOUR V-01 baseline: failing NODE-ID set UNCHANGED and passed count up by exactly the number of tests added. Paste `aw sanitize --agent` and its exit code.
  - Observed evidence:
    (1) New test names in tests/test_attention.py under InboxAgentEvidenceTests:
    - test_compact_agent_record_contains_inbox_waiting_count
    - test_drained_inbox_omits_inbox_waiting_key
    - test_findings_equal_between_populated_and_drained_records
    - test_verbose_agent_record_contains_inbox_waiting_number
    - test_check_agent_stays_silent_with_waiting_drops

    Passing run of targeted 4-suite run:
    $ python3 -m pytest tests/test_attention.py tests/test_attention_contract.py tests/test_prompts_attention.py tests/test_attention_blind_spot.py -o addopts=""
    111 passed in 19.83s (baseline was 106 passed; count increased by exactly 5).

    (2) Test asserting findings EQUALITY in full:
    ```python
    def test_findings_equal_between_populated_and_drained_records(self):
        """Case 3: THE CONTRACT CASE: `findings` is EQUAL between the drops-present and drained records.

        This is the assertion that would fail had route (b) been taken, where a warning Diagnostic
        inflates findings on a clean repo.
        """
        box = self._inbox()
        (box / "README.md").write_text("what this lane is", encoding="utf-8")
        (box / ".gitkeep").write_text("", encoding="utf-8")
        drained_rec = self._run_agent()

        (box / "drop1.md").write_text("x", encoding="utf-8")
        (box / "drop2.md").write_text("x", encoding="utf-8")
        populated_rec = self._run_agent()

        self.assertEqual(
            populated_rec.get("findings"),
            drained_rec.get("findings"),
            "findings must be equal between populated and drained inboxes",
        )
        self.assertEqual(populated_rec.get("outcome"), drained_rec.get("outcome"))
        self.assertEqual(populated_rec.get("exit"), drained_rec.get("exit"))
        self.assertEqual(populated_rec.get("verified"), drained_rec.get("verified"))
        self.assertEqual(populated_rec.get("complete"), drained_rec.get("complete"))
        self.assertEqual(populated_rec.get("cmd"), drained_rec.get("cmd"))
        self.assertEqual(populated_rec.get("schema"), drained_rec.get("schema"))
    ```
    Passing output:
    $ python3 -m pytest tests/test_attention.py -k test_findings_equal_between_populated_and_drained_records -v
    1 passed in 4.52s

    Proof it bites under route (b):
    Evaluating the equality assertion against a CommandResult with Diagnostic(severity="warning"):
    route_b_rec["findings"] == 1, drained_rec["findings"] == 0
    AssertionError: 1 != 0 : findings must be equal between populated and drained inboxes

    (3) --check --agent case:
    $ python3 -m pytest tests/test_attention.py -k test_check_agent_stays_silent_with_waiting_drops -v
    1 passed in 4.38s
    (evidence is ["attention"], findings=0, exit=0, outcome='clean', no inbox-waiting).

    (4) Grep over new tests proving no reference to real .aw/inbox/ and no inspect/ast/regex:
    Matches for real .aw/inbox/: none
    Matches for inspect/ast/regex on attention.py: none

    (5) git diff --stat tests/test_attention_contract.py:
    Empty (0 files changed, completely unmodified).

    (6) Full bare python3 -m pytest summary:
    $ python3 -m pytest
    6435 passed, 2 skipped, 3 warnings in 408.45s (0:06:48) [258 deselected]
    Delta against V-01 baseline (6430 passed): exactly +5 passed, 0 failures, failing node-id set unchanged ([]).

    (7) aw sanitize --agent:
    $ python3 -m agent_workflows sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    Exit code: 0
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, which is correct and deliberate: that field is an OUTPUT of `/plan-review` and an authored value would forge a review that has not happened. It requires explicit human approval before execution.

EXECUTION CONTRACT. Commit ONLY the two declared paths, through `aw commit <plan> -- agent_workflows/attention.py tests/test_attention.py`; never `git add -A`, never `-a`, never `--no-verify`, and never push. This is a shared checkout, so verify the staged set with `git diff --cached --name-only` before every commit and unstage anything that is not yours with `git restore --staged <path>`. Paste ACTUAL runner output for every test claim; do not fix the pre-existing failures F-07 names, which are outside both declared paths and are another party's.

STOP CONDITIONS ARE REAL AND E-01 OWNS THEM. If the severity-blind `findings` tally has been fixed, route (b) becomes the cheaper answer following a precedent already inside `attention.run`, and this plan should be re-reviewed rather than executed as written. If a scalar `Evidence` value no longer survives compaction, the chosen route no longer delivers a visible number and executing it would ship the exact invisibility the backlog item complains about. Report either rather than adapting silently.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and EVERY `V-*` item is verified with concrete pasted evidence. Under `aw oc run` / `aw agy run` the RUNNER owns `aw ipd begin`/`aw ipd finalize` and the executor must NOT run them; it leaves every `V-*` at `Result: pass` with pasted evidence and the pre-transition lint conforming. Executed by hand with no runner, the executor performs the transition through `aw ipd finalize` (per the `ipd-lifecycle` workflow), never by hand-editing the status or moving the file. Because this plan's Set contains a plan (`9iiqmm`) that once self-finalized with an empty diff, confirm the work actually landed before finalizing: run `git show HEAD:agent_workflows/attention.py | grep -c 'inbox-waiting' || true` and read the printed NUMBER (never the exit status, since `grep -c` exits 1 on a zero count), confirming it is nonzero.

BACKLOG CLOSE. This plan graduates `xqem10`, which carries NO `- Blocks-Release:` gate, so no release-gate handoff is required. The item also remains the named carrier for OQ-01, so do NOT close it in a way that discards that residue: the runner sets `graduated` on verification, which is the correct state, and a `done` close is not this plan's to perform.
