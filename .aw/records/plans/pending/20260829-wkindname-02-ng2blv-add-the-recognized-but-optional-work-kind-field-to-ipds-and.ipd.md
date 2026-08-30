# IPD: add the recognized-but-optional Work-Kind field to IPDs and specs

- Date: 2026-08-29
- Kind: child
- Concern: Plans and specs have no field recording the NATURE of the work (bug, feature, chore, security, followup), so that classification is lost the moment a backlog item graduates into a plan. The field cannot be called `Kind`: plans already use `Kind` for their structural role (orchestrator or child) and research uses it for document type, so the name is `Work-Kind`, matching what child 01 renamed backlog's field to.
- Scope: Add a recognized-but-optional `Work-Kind` field to the IPD schema and the spec contract, reusing backlog's existing vocabulary rather than forking it, with setter support on the existing verbs and an `aw check` enum rule. Excludes renaming or migrating backlog (child 01 owns that, and this plan requires it executed), excludes adding the field to research, excludes attention-board wiring or sort changes, and excludes deriving the value from `From-Backlog`.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/specs.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/status_set.py, tests/test_work_kind.py
- Item-Dependencies: executed:9trlc3
- Status: to-review
- Set: wkindname
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: ng2blv
- Blocks-Release: next
- From-Backlog: 1ap48y

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 /plan-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-001/PR-004 applied here as new F11/F12, plus a refreshed baseline. This plan needed the LEAST work of the three and its inherited findings were independently re-verified rather than trusted: `backlog.KINDS` is exactly `{bug,feature,chore,security,followup}` with NO second definition anywhere in `agent_workflows/`; the `Kind` collision is real and is in fact FOURFOLD, not threefold, since `comms.KINDS` (`ask|reply|task|handoff|fyi`) is a further disjoint use the plan did not count; `META_PRIORITY` sits in `META_RECOGNIZED` and not `META_REQUIRED`, which is the optional shape E-02 copies; `check.priority-invalid` is registered as claimed; and F9's `59` undeclared-leaf failure was RE-MEASURED at `be49ac4` and is unchanged, confirming the plan's no-worsening requirement is still calibrated and its warning about the `slow` marker still correct (a bare run reports `no tests ran` for that module). The fixes are about REPORTING, not code, since this plan was always adding an optional field. F11: the Set's premise that the field is "optional on all three so an artifact without it still validates" is FALSE for backlog, which requires it today and keeps requiring it after child 01's pure rename, so the delivered outcome is one NAME on three types plus optional mechanics on two; a V-item asserting otherwise could not be satisfied honestly, and an executor trying to satisfy it would have to weaken backlog's contract, which this plan's fence forbids. F12: "one `aw check` rule flags each type" conflates two mechanisms, since backlog reports through its pre-existing `backlog.kind-invalid` contract drift while this plan's `check.work-kind-invalid` covers only plans and specs; V-05 no longer extends its absent-field claim to backlog. Stale baseline refreshed: fast suite `2927 passed, 3 skipped, 4 xfailed` at `be49ac4` (the recorded `2880` at `df731f1` was already stale, illustrating the plan's own rule). Lints `conforming` at review-finalize with zero diagnostics and zero advisories. No E-item text changed; OQ-01 and OQ-02 unchanged. Dependency gate on `executed:9trlc3` verified intact.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): split out of the approved plan `a6cej0` (now superseded) at the maintainer's direction, carrying its field-addition work unchanged along with the findings a prior `/plan-review` added to it. The rename half became child 01 (`9trlc3`), which this plan declares as an executed dependency: the field name recognized here must already be the name backlog writes, or the tree would briefly carry two spellings for one concept. All E-item and V-item text below is inherited from the reviewed `a6cej0` rather than re-authored, so the review's resolutions (notably that `aw ipd scaffold` needs no flag and that the command-surface declaration list must not gain one) are preserved.

## Goal

Let a work item's nature survive graduation. A bug filed in the backlog stays identifiable as a bug once it becomes a plan or a spec, on one shared vocabulary and with the same recognized-but-optional mechanics the `Priority` field already established, so nothing existing is mass-failed.

Scope note on OPTIONALITY, so the Set's outcome is not overstated: recognized-but-optional applies to the two carriers THIS plan adds. Backlog REQUIRES its work-nature field today and child 01 is a pure rename that preserves that, so the Set delivers one NAME across three types, not one requiredness. Do not describe the result as "optional on all three", and do not touch backlog to make that true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared vocabulary, recognized in two contracts

- [ ] E-01 Export backlog's work-nature vocabulary as the ONE shared source and do not fork it. `backlog.KINDS` already exists as a frozenset of `bug`, `feature`, `chore`, `security`, `followup`. Consume THAT from the plan and spec contracts exactly as `backlog.PRIORITIES` is consumed today by `ipd_schema`, `specs`, `check_engine`, `releases`, and `research_cmd` (locate those consumers by grepping for `PRIORITIES` to copy the established import pattern). Do NOT define a second tuple and do NOT define a per-type subset. The vocabulary SYMBOL `backlog.KINDS` keeps its name (only the on-disk FIELD was renamed, by child 01 `9trlc3`), so do not rename the symbol either. If the executor believes a shared SUPERSET is needed (see OQ-01's resolution, which rejects this), that is a scope question to report rather than a silent addition.
  - Depends on: none
  - Expected outcome: one vocabulary symbol is imported by every new consumer; a grep for the member tokens shows no second literal list; the `backlog.KINDS` symbol name is unchanged.
  - Execution state: pending

- [ ] E-02 Recognize `Work-Kind` in the IPD schema as recognized-but-OPTIONAL, mirroring `META_PRIORITY` exactly: add the field constant and include it in `META_RECOGNIZED` but NOT in `META_REQUIRED`. Constraints, all inherited from the `META_PRIORITY` comment rather than invented here: recognition exists only to stop the unknown-field lint error, the ENUM value check belongs to `aw check` (E-05) and must NOT be added to the schema, and absent means unclassified with no forced default. The name is `Work-Kind` and not `Kind` because of the hard collision recorded in F2.
  - Depends on: E-01
  - Expected outcome: a plan carrying a valid `- Work-Kind:` lints clean; a plan carrying NONE lints clean (no mass-fail); the field is absent from `META_REQUIRED`; no enum validation was added to the schema layer.
  - Execution state: pending

- [ ] E-03 Recognize `- Work-Kind:` on a spec, mirroring the spec contract's existing optional `- Priority:` handling. Add the bullet regex and reader alongside `_PRIORITY_RE` and its reader (locate both by symbol), keeping the same shape: present-and-valid passes, present-and-invalid is reported by `aw check`, absent returns None and is silent. Note the spec-vocabulary concern the item raises, that a spec is rarely a "bug" and reads more like design or policy: OQ-01 resolves this by keeping ONE vocabulary and accepting that specs will mostly use `feature` or `chore`, because forking a per-type vocabulary is the exact drift the item itself warns against and the `xprio` precedent explicitly forbade ("do NOT fork three copies").
  - Depends on: E-01
  - Expected outcome: a spec with a valid `- Work-Kind:` passes `aw specs check`; a spec with none passes unchanged; the reader returns None when absent.
  - Execution state: pending

### Task group 2: setters and validation

- [ ] E-04 Add setter support so the field is never hand-written, since the house rule is that conforming artifacts are created and mutated by verbs. Extend `aw ipd set` and `aw specs set` with a `--work-kind` option accepting a vocabulary member or `-` to clear, exactly mirroring how `--blocks-release` and `--priority` already behave on those verbs (locate the existing `--priority` wiring in `cli.py` and the write path in `status_set.py` and `specs.py`, and copy it). Do NOT add the option to `aw ipd scaffold`: the conditional this E-item used to leave open is RESOLVED by measurement (F10), since `aw ipd scaffold --help` carries NO `--priority`, so the "if and only if" condition is FALSE. Do NOT add a new standalone verb. Do NOT add `--work-kind` to `command_surface.py`'s `legacy_flags`: per F8 that tuple is not asserted exhaustive and the `Priority` precedent left `--priority` undeclared on both verbs, so declaring only this one field would be a gratuitous asymmetry and would pull an undeclared file into scope.
  - Depends on: E-02, E-03
  - Expected outcome: `aw ipd set <status> <plan> --work-kind bug` writes the field; `--work-kind -` clears it; the same for `aw specs set`; an out-of-vocab value is rejected by the setter with a nonzero exit; the flag's shape matches `--priority`.
  - Execution state: pending

- [ ] E-05 Add a `check.work-kind-invalid` rule to the `aw check` registry and implement it, using `check.priority-invalid` as a line-by-line template (same severity, assurance class, and determinism: error, repository, deterministic). Behavior: an out-of-vocab value is an error, an ABSENT field is silent. Constraints: reuse E-01's shared vocabulary in the message so accepted and advertised values cannot drift, and keep the validation in the registry rather than the schema or spec contract, which is where the `Priority` precedent puts it.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `aw check` flags a plan and a spec carrying an out-of-vocab `Work-Kind` with `check.work-kind-invalid`; artifacts with a valid value or NO value produce no finding; the rule appears in the registry with the same class as its `Priority` sibling.
  - Execution state: pending

- [ ] E-06 Add `tests/test_work_kind.py`, modeled on the EXISTING `tests/test_ipd_priority.py` and `tests/test_spec_priority.py` (both present; read them first and mirror their structure so the two features are verified the same way). Cover: a valid `Work-Kind` on a plan and on a spec passes lint/check; an ABSENT field passes, which is the no-mass-fail property and must be asserted for BOTH types; an out-of-vocab value produces exactly `check.work-kind-invalid`; the setter writes, clears, and rejects; and a SINGLE-VOCABULARY assertion proving the accepted set is `backlog.KINDS` itself rather than a copy, so a future fork fails the suite. Add one assertion that the field is NOT in `META_REQUIRED`, since that is the property protecting the existing corpus.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the module passes; the absent-field cases fail against an implementation that made the field required; the single-vocabulary assertion fails against a forked list.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PRECEDENT IS EXECUTED, NOT HYPOTHETICAL, and it is the single most important fact for this plan. The item names `Priority` (Set `xprio`) as the pattern to follow; that Set is COMPLETE in `executed/` as an orchestrator plus three per-type children (plans, specs, research). Its orchestrator states the rules this plan inherits verbatim: recognized-but-OPTIONAL everywhere "so existing artifacts are not mass-failed", "ABSENT = unprioritized (do not force a default)", and "Reuse ONE shared vocab ... do not fork three copies". This plan is the same change for a different field.
- The layering rule is explicit in the schema's own comments and must be followed: the schema RECOGNIZES a field only to stop the unknown-field lint error, while the ENUM check lives in the `aw check` surface. This is stated for `Priority`, `Scope-Paths`, `Blocks-Release`, and `From-Backlog` alike.
- `backlog.KINDS` already exists with exactly the item's proposed vocabulary (`bug`, `feature`, `chore`, `security`, `followup`), so no vocabulary needs designing. `backlog.PRIORITIES` shows the shared-consumption pattern to copy, with consumers in `ipd_schema`, `specs`, `check_engine`, `releases`, and `research_cmd`.
- `check.priority-invalid` is registered as (error, repository, deterministic) and its implementation reads the value, passes it against the shared vocabulary, and stays silent when absent. E-05 copies this shape.
- Test precedents EXIST for this exact kind of field: `tests/test_ipd_priority.py` and `tests/test_spec_priority.py`. Mirror them rather than inventing a test shape.
- The `Kind` token is genuinely triple-booked, which is what makes `Work-Kind` the right name rather than a stylistic choice. `ipd_schema.KINDS` is `{child, orchestrator}` for an IPD's REQUIRED structural `Kind`; `research_contract.KINDS` is an 18-member document-type vocabulary (`research-prompt`, `findings`, `survey`, and so on) with its own documented extension mechanism; and `backlog.KINDS` is the work-nature set. All three are disjoint.
- The attention board already renders an optional label type-agnostically and its shared sort key deliberately excludes such fields for every tree. The `xprio` Set added LABELING only and left the sort key alone on purpose. This plan adds NO board wiring at all (see Deferred), so it must not touch either.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `.aw/records/plans/executed/`, Set `xprio` | The item's named precedent is ALREADY EXECUTED and supplies a complete template (orchestrator `u5vyye` plus children `1b45el` plans, `rp859c` specs, `6vgd0k` research), including the exact rules this plan needs: optional-not-required, absent means unset, one shared vocabulary, no sort-key change. This converts the item's four "resolve at plan time" questions into "follow the proven pattern". | the four `xprio` files in `executed/`; the orchestrator's Scope and Completion criteria state each rule verbatim |
| F2 | HIGH | `ipd_schema.KINDS`; `research_contract.KINDS`; `backlog.KINDS` | The `Kind` collision is REAL and threefold, which validates the item's naming decision on evidence rather than taste. `ipd_schema.KINDS` is `{child, orchestrator}` and backs a REQUIRED structural field; `research_contract.KINDS` is an 18-member document-type set with its own extension mechanism; `backlog.KINDS` is the work-nature set. Reusing `Kind` for work-nature on an IPD would put two disjoint vocabularies behind one token on the same artifact. | the three definitions read at `d4dbbaf` |
| F3 | MED | `backlog.KINDS` | No vocabulary design is needed: the item's proposed member set already exists in code as exactly `{bug, feature, chore, security, followup}`. E-01 reuses it directly. | `KINDS = frozenset(("bug", "feature", "chore", "security", "followup"))` |
| F4 | MED | `check_engine` rule registry; `ipd_schema` comments | The recognized-but-optional MECHANICS are fully specified by precedent, so the item's design consideration 4 needs no decision: recognition goes in `META_RECOGNIZED` and NOT `META_REQUIRED` (so nothing is mass-failed), and the enum check goes in the `aw check` registry as (error, repository, deterministic). | `check.priority-invalid` RuleSpec; the `META_PRIORITY` comment stating the enum check "lives in the `aw check` surface ... NOT the schema layer" |
| F5 | MED | `attention.py`, `check_engine.py` | A CORRECTION TO THE ITEM'S STATED BENEFIT. The item says the missing field means `aw attention` and queries "can't filter all bug work across trees", implying backlog's `Kind` is consumed today. It is NOT: nothing reads a work-nature field anywhere, and the attention `Item` record carries `priority` and `blocks_release` but no kind at all. So this plan makes the classification RECORDED AND VALIDATED on two more types; it does NOT deliver cross-tree filtering, and the executor must not claim it does. Filtering would be a separate change against the board and the query surface. | attention `Item` fields; no consumer of `backlog.KINDS` outside backlog's own validation and `new` |
| F6 | LOW | the item's design consideration 2 | DERIVING the value from `From-Backlog` is available in principle (a shared resolver `find_from_backlog_artifacts` exists, and `From-Backlog` is already a recognized plan field), but it is rejected for this plan; see OQ-02. Recording that it is POSSIBLE matters so a reviewer knows the option was evaluated rather than overlooked. | `check_engine.find_from_backlog_plans` / `find_from_backlog_specs` / `find_from_backlog_artifacts` |
| F8 | MED | `tests/test_command_surface_declarations.py`; `agent_workflows/command_surface.py` | THE SCOPE-CHECK'S "CHECK THIS BEFORE STARTING" TASK IS NOW RESOLVED, so the executor does not have to discover it under time pressure, and the answer removes a scope risk rather than adding one. An OPTION does NOT trigger the undeclared-leaf requirement: `find_undeclared_leaves` compares parser LEAVES (subcommands) against `COMMAND_INVENTORY` and never inspects flags, so adding `--work-kind` to two existing verbs cannot create an undeclared leaf. Separately, `COMMAND_INVENTORY` does carry a per-command `legacy_flags` tuple, and the honest precedent is that `xprio` did NOT update it: `aw ipd set` and `aw specs set` both ACCEPT `--priority` today while neither declares it in `legacy_flags`. Nothing asserts that tuple is exhaustive (no test references `legacy_flags` except one `--json` membership check in `tests/conformance_matrix.py`), so omitting `--work-kind` there matches the sibling field exactly. CONCLUSION: `command_surface.py` stays OUT of scope, matching the fence as written. | measured at `770be84`: `find_undeclared_leaves` body compares `discover_parser_leaves(parser) - get_declared_leaves()`; `aw ipd set --help` lists `--priority` while `command_surface.py:714-723` omits it; `sed` of `specs set` `legacy_flags` yields 0 matches for priority; `grep -rn legacy_flags tests/` finds only `conformance_matrix.py:89` |
| F9 | MED | `tests/test_command_surface_declarations.py` | THE PRE-EXISTING FAILURE THE PLAN WARNS ABOUT IS REAL, MEASURED, AND ALREADY 59 STRONG, and it is INVISIBLE to the plan's own prescribed commands. `test_zero_undeclared_parser_leaves` fails with `59 != 0`, listing leaves such as `oc run`, `agy run`, `runs`, `commit`, `completion`, and `work begin`. Critically, the module is `pytestmark = pytest.mark.slow`, and this repo's addopts include `-m 'not slow'`, so the plan's prescribed bare `python3 -m pytest` NEVER RUNS IT and the executor would see a clean run while the conformance suite is red. It surfaces only under `-m ""` or `make test-all`. The plan already asks the executor to attribute pre-existing failures by name; this finding supplies the baseline so that attribution is checkable rather than a promise, and it means "the CLI-surface conformance tests must pass" was an unrunnable requirement as written. | measured at `770be84`: `python3 -m pytest tests/test_command_surface_declarations.py` reports `no tests ran`; with `-m ""` it reports `1 failed, 13 passed` and `AssertionError: 59 != 0`; `pytestmark = pytest.mark.slow` at `tests/test_command_surface_declarations.py:37`; `addopts = "-q -n auto --dist=worksteal -m 'not slow'"` at `pyproject.toml:122` |
| F11 | MED | `backlog.py:178`; `ipd_schema.py:199` | THE SET'S SHARED PREMISE WAS PARTLY FALSE AND THIS PLAN INHERITED THE WORDING. The orchestrator promised the field would be optional "on all three so an artifact without it still validates". That is true for the two types THIS plan adds and false for backlog, which validates the field on read and rejects an absent value today; child 01 is a pure rename and preserves that. So the delivered outcome is one NAME on three types plus optional mechanics on two of them. This plan's own code is unaffected (it was always adding an optional field), but its REPORTING is: a V-item pasting "absent validates on all three" cannot be satisfied honestly, and an executor trying to satisfy it would have to weaken backlog's contract, which this plan's fence forbids. | measured at `be49ac4`: a backlog item with no work-nature field yields `backlog.kind-invalid ... : None`, exit 1; `META_PRIORITY` is in `META_RECOGNIZED` and NOT `META_REQUIRED`, the optional shape this plan copies |
| F12 | LOW | `check_engine.py:143`; `backlog.py:178` | Related to F11 and worth stating because the Set's criteria said "`aw check` flags an out-of-vocabulary value on each type" as if one rule covered all three. It does not: this plan's new `check.work-kind-invalid` covers plans and specs, while backlog reports through its own pre-existing contract-drift path `backlog.kind-invalid`. Nothing routes backlog through the registry and this plan must not add such routing. Two mechanisms, by design. | `backlog.py:178` emits `core.Drift(..., "backlog.kind-invalid", ...)`; the registry template this plan copies is `"check.priority-invalid": RuleSpec(...)` at `check_engine.py:143` |
| F10 | LOW | `aw ipd scaffold`; `.aw/records/specs/20260726-1340-01-ipd-spec.spec.md` | TWO MORE OF THE PLAN'S DEFERRED-TO-EXECUTOR CHECKS ARE RESOLVED HERE, both to "do nothing", which shrinks the change. First, E-04's conditional ("add to `aw ipd scaffold` if and only if `--priority` is already there"): `aw ipd scaffold --help` has NO `--priority`, so the condition is FALSE and `--work-kind` must NOT be added there. Second, the Spec/documentation-sync conditional (does `ipd-spec` enumerate recognized metadata fields, and was `Priority` added when `xprio` landed): `ipd-spec` contains ZERO occurrences of `Priority`, so it does not enumerate these optional fields and no spec edit is owed. Both answers preserve the plan's own instruction to follow the `Priority` precedent rather than invent an obligation. | measured at `770be84`: `aw ipd scaffold --help | grep -i priority` returns nothing (exit 1); `grep -c Priority .aw/records/specs/20260726-1340-01-ipd-spec.spec.md` returns 0 |

## Proposed changes (ordered, validatable)

1. Reuse backlog's vocabulary as the one shared source (E-01).
2. Recognize `Work-Kind` in the IPD schema as optional, with no schema-level enum check (E-02).
3. Recognize `- Work-Kind:` on specs alongside the existing optional `Priority` (E-03).
4. Add `--work-kind` to the existing setters, mirroring `--priority` (E-04).
5. Register and implement `check.work-kind-invalid` following `check.priority-invalid` (E-05).
6. Prove it with tests mirroring the existing priority test modules (E-06).

## Deferred / out of scope (with reason)

- Renaming and migrating backlog's own field is child 01 (`9trlc3`), declared here as `executed:9trlc3`. This plan must not touch `backlog.py` or the backlog records tree; it only IMPORTS the vocabulary.
- Adding `Work-Kind` to RESEARCH. A research document's nature is already carried by its mandatory document-type facet drawn from an 18-member vocabulary, so a second kind axis there would confuse rather than clarify. This is where the Set deliberately differs from `xprio`, which included research because priority is orthogonal to document type.
- DERIVING the value from `From-Backlog`. A derived value is undefined for the majority of artifacts that carry no such link and would let a plan's classification change silently when someone edits the source item. Because the field is optional, a later derivation pass can populate absent values without contradicting this plan.
- ATTENTION-BOARD wiring, labelling, and any sort-key change, and therefore cross-tree FILTERING. Nothing consumes a work-nature field today; delivering search is separate work and this plan must not claim it.
- BACKFILLING the field onto existing plans and specs. Absent means unclassified by design.

## Scope check

- Over-scope: none. The schema carries E-02, the spec contract E-03, the check engine E-05, the CLI and setter module E-04, and the test file is new.
- `agent_workflows/backlog.py` is deliberately NOT declared. This plan only imports the vocabulary symbol from it; child 01 owns every edit to that module. If the executor finds itself editing `backlog.py`, the Set's division has been breached and it must STOP and report.
- Under-scope: none outstanding. The two questions the earlier plan deferred to the executor were resolved at review and are recorded in the findings: `aw ipd scaffold` needs no new flag, and the command-surface declaration list must not gain one either.
- `cli.py` is among the most contended files in this checkout and had unrelated changes STAGED by another session while this plan was authored. Re-read it immediately before editing and verify the staged set before committing.

## Required tests / validation

- `tests/test_work_kind.py` must pass with every case in E-06. Falsifiability is specific: the absent-field cases must FAIL against an implementation that added the field to `META_REQUIRED`; the single-vocabulary assertion must FAIL against a forked literal list; the out-of-vocab case must FAIL against an implementation with no `aw check` rule.
- The EXISTING `tests/test_ipd_priority.py` and `tests/test_spec_priority.py` must pass UNCHANGED. They are the sibling feature's tests and touch the same schema and spec-contract code paths, so a regression there means E-02 or E-03 disturbed `Priority`. Neither file is in `Scope-Paths`.
- `aw check` must run clean on THIS repo's existing corpus after the change, which is the concrete proof of the no-mass-fail property: no existing plan or spec carries `Work-Kind`, so a correct optional implementation produces ZERO new findings. Paste the before and after counts.
- The CLI-surface conformance tests: `test_zero_undeclared_parser_leaves` is ALREADY FAILING with `59 != 0` at `770be84` (F9), so "must pass" is not achievable and is not this plan's job. The requirement is instead a NO-WORSENING one, and it must be measured deliberately because the module is marked `slow` and the fast suite SKIPS it entirely: run `python3 -m pytest tests/test_command_surface_declarations.py -m ""` before and after your change and paste both undeclared-leaf COUNTS. The count must not increase, and no leaf naming `work-kind` may appear. Per F8 an option cannot create a leaf, so an increase here means something unintended was added.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`. NOTE that the two invocations are NOT interchangeable for this plan: the bare run excludes `-m 'not slow'` content, which is exactly where the CLI-surface conformance module lives, so a clean bare run says NOTHING about it.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite at `be49ac4` during this review: `2927 passed, 3 skipped, 4 xfailed`. The `2880` reading at `df731f1` recorded when this plan was authored is already stale, which is exactly why the rule exists. Take your own before/after readings with their HEAD; concurrent agents are committing to `cli.py` and `check_engine.py`. The `59` undeclared-leaf baseline in F9 was independently RE-MEASURED at `be49ac4` and is unchanged, so it remains a usable comparison point.
- End-to-end: set `Work-Kind` on a real plan and a real spec with the new setters, paste the resulting metadata lines, run `aw check` clean, then clear both with `--work-kind -` and show the lines are gone. Use artifacts you own or a fixture; do not modify another agent's in-flight plan.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- No spec text change is required. This plan adds an optional metadata field following an already-executed pattern and changes no contract a spec pins.
- Whether the `ipd-spec` document enumerates recognized metadata fields was checked at review and the answer is recorded in the findings: follow whatever the `Priority` precedent did there, and do not invent a new documentation obligation.
- Record in the terminal history that ONE field name now spans backlog, plans, and specs, and that nothing yet consumes it for filtering.

## Open questions

### OQ-01: One shared vocabulary across all types, or a per-type appropriate set?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONE SHARED VOCABULARY, reused unchanged. Inherited from the superseded `a6cej0` and unchanged by the split. A spec is rarely a "bug" and reads more like design or policy, which tempts a per-type set, but the mechanism that actually produces drift in this codebase is FORKED definitions, which is why the executed `xprio` Set's completion criteria demand one shared vocabulary provable by grep. A per-type set is exactly such a fork. The existing five members cover the realistic spec cases adequately: a spec proposing new capability is `feature`, one codifying convention is `chore`. Accepted cost, recorded rather than hidden: `security` and `followup` will rarely apply to specs. If a real gap appears the fix is ONE new member in the ONE shared set.

### OQ-02: Store `Work-Kind` explicitly, or derive it from `From-Backlog`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: STORE EXPLICITLY. Inherited from the superseded `a6cej0`. Deriving is mechanically possible, since `From-Backlog` is already a recognized plan field and a shared resolver exists, but a derived value would be UNDEFINED for the majority of artifacts that carry no such link, so it could never be the primary mechanism. Worse, it would make a plan's work nature depend on another artifact's current content, so the classification could change silently when someone edits the source backlog item. An explicit-overrides-derived hybrid is the most complex option for the least certain benefit. Because the field is optional and absent means unclassified, a later derivation pass can populate absent values without contradicting this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the import of the shared vocabulary in every new consumer. Then paste a grep for the member tokens (`bug`, `feature`, `chore`, `security`, `followup` as a literal collection) proving there is NO second definition anywhere in `agent_workflows/`. Paste `git diff` for `backlog.py` showing it is EMPTY, since that file is deliberately undeclared and unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new schema constant and its inclusion in `META_RECOGNIZED`, plus proof it is NOT in `META_REQUIRED`. Paste a lint run on a plan WITH a valid `Work-Kind` and on a plan WITHOUT one, both conforming. Confirm by inspection that no enum validation was added to the schema layer, matching the layering comment the schema states for `Priority`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the spec-side regex and reader next to the existing `Priority` equivalents to show the shape matches. Paste `aw specs check` passing for a spec with a valid value and for one with none, and the reader returning None when absent.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw ipd set ... --work-kind bug` writing the line, `--work-kind -` clearing it, and an out-of-vocab value REJECTED with a nonzero exit and no write. Same three for `aw specs set`. Confirm `aw ipd scaffold` was NOT given the option, and paste `aw ipd scaffold --help` showing it still has no `--priority` either (F10's condition, re-measured rather than trusted). Paste the undeclared-leaf COUNT from `python3 -m pytest tests/test_command_surface_declarations.py -m ""` before and after, showing it did not increase from the `59` baseline measured at `770be84` and that no leaf names `work-kind`; a clean BARE run is not acceptable evidence here because the module is `slow`-marked and the bare run skips it (F9). Confirm `command_surface.py` was not edited.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new registry entry beside `check.priority-invalid` showing the same severity, assurance class, and determinism. Paste `aw check` flagging an out-of-vocab value on a PLAN and on a SPEC with rule `check.work-kind-invalid`. Paste `aw check` producing NO finding for a valid value and NO finding for an absent field ON THOSE TWO TYPES; do not extend the claim to backlog, which keeps requiring the field and reports through `backlog.kind-invalid` (F11/F12). Then paste the whole-repo proof: `aw check` finding counts before and after the change on this repo's real corpus, showing ZERO new findings (the no-mass-fail property).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the full new module passing. Paste FALSIFIABILITY as actual failures: the absent-field cases failing when the field is made required, and the single-vocabulary assertion failing against a forked list. Paste `tests/test_ipd_priority.py` and `tests/test_spec_priority.py` passing UNCHANGED, since a break there means the sibling field was disturbed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, well under the thresholds of 18 leaves and 5 groups. One concern throughout: give plans and specs the optional work-nature field. Right-sizing per leaf: E-01 the shared vocabulary, E-02 the plan contract, E-03 the spec contract, E-04 the setters, E-05 the check rule, E-06 the tests.

Open questions: ALL RESOLVED, and none needs a maintainer decision. OQ-01 keeps one shared vocabulary; OQ-02 stores rather than derives. The two decisions the maintainer made for this Set (rename first, and one consistent field name) are implemented by child 01 and assumed here.

DEPENDENCY GATE: this plan declares `executed:9trlc3` and may NOT run before child 01 has executed. The reason is naming coherence rather than a code dependency, since the two plans touch disjoint modules: if this landed while backlog still wrote the old spelling, the tree would carry two names for one concept, which is what the Set exists to remove. Verify child 01 is in `executed/` before starting.

Scope fence: touch ONLY `agent_workflows/ipd_schema.py`, `agent_workflows/specs.py`, `agent_workflows/check_engine.py`, `agent_workflows/cli.py`, `agent_workflows/status_set.py`, and the new `tests/test_work_kind.py`. Do NOT touch `agent_workflows/backlog.py` or the backlog records tree (child 01 owns them; importing the vocabulary is fine, editing is not), do NOT touch `agent_workflows/attention.py` or any sort key, do NOT add the field to research, do NOT edit the existing priority test modules (they must stay green unedited), and do NOT backfill the field onto existing artifacts. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured. Specific to this plan: do NOT describe the outcome as enabling cross-tree filtering or search, because nothing consumes the field yet.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT with several concurrent sessions; `cli.py` and `check_engine.py` are both actively contended and one session had unrelated files staged while this was authored, so verify the staged set rather than trusting the path scope. Locate insertion points by how `Priority` is wired rather than by line number.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
