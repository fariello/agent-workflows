# IPD: add a uniform recognized-but-optional Work-Kind field to IPDs and specs, reusing backlog's vocabulary

- Date: 2026-08-29
- Kind: child
- Concern: Only BACKLOG classifies the NATURE of work (`- Kind: bug|feature|chore|security|followup`). IPDs and specs have no such field, so a bug-versus-feature classification is LOST the moment a backlog item graduates into a plan, and no query can ask for "all bug work" across trees. The field cannot simply be called `Kind`, because that token is already taken twice: an IPD's structural `Kind: orchestrator|child` and research's document-type kind, whose vocabularies are entirely disjoint from backlog's.
- Scope: Add a uniform recognized-but-optional `Work-Kind` field to IPDs and specs, reusing backlog's existing work-nature vocabulary rather than forking it, with setter support and an `aw check` enum rule, following the `Priority` precedent exactly. Excludes renaming backlog's own `Kind` field, excludes adding `Work-Kind` to research, excludes any attention-board sort change, and excludes deriving the value from `From-Backlog`.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/specs.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/status_set.py, tests/test_work_kind.py
- Item-Dependencies: none
- Status: approved
- Set: workkind
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: a6cej0
- Approval: 2026-08-30, recorded via aw ipd set: status set to approved
- Blocks-Release: next
- From-Backlog: 1ap48y

## Workflow history
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-30 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Strongest of three plans in this sweep: every substantive claim VERIFIED, including backlog.KINDS being exactly {bug,feature,chore,security,followup}, the genuinely THREEFOLD Kind collision (ipd_schema {child,orchestrator}, research_contract 18 members, backlog work-nature), the xprio Set executed as orchestrator plus three children, the META_PRIORITY comment stating verbatim that the enum check lives in the aw check surface NOT the schema layer, check.priority-invalid registered (error, repository, deterministic), and both priority test modules present and passing (14 passed). F5's correction independently CONFIRMED and is the plan's best insight: backlog.KINDS is consumed only by backlog's own validation and new verb, and attention.Item carries priority and blocks_release but NO kind, so this plan delivers a recorded+validated field and NOT cross-tree filtering. PR-001 (MEDIUM, new F9): the CLI-conformance requirement was UNRUNNABLE. test_zero_undeclared_parser_leaves already fails 59 != 0 and the module is slow-marked while addopts carry -m 'not slow', so the plan's own prescribed bare pytest reports 'no tests ran' and an executor would see green while the suite is red; replaced with a measured no-worsening check against the pasted baseline. PR-002 (MEDIUM, new F8): resolved the scope-check's open pre-work task, and it REMOVES risk: an option cannot trigger the undeclared-leaf requirement (find_undeclared_leaves compares subcommand leaves only), and legacy_flags is not asserted exhaustive since xprio left --priority undeclared on both ipd set and specs set, so command_surface.py stays out of scope. PR-003 (LOW, new F10): resolved two more deferred conditionals to 'do nothing' (aw ipd scaffold has no --priority; ipd-spec has zero Priority mentions). PR-004 (LOW): recorded two deliberate precedent divergences, that xprio wired attention.py while this plan does not (Work-Kind will appear nowhere in aw attention output) and that omitting import-only backlog.py improves on xprio's needless in-scope-unmodified reconciliation. No open questions remain.

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `1ap48y` during the blocking-backlog graduation sweep. All four of the item's "resolve at plan time, do NOT assume" design questions are RESOLVED here from repository evidence, not deferred: the vocabulary question, the derive-versus-store question, the backlog-reconciliation question, and the recognized-but-optional mechanics. The decisive evidence is that the item's own named precedent, the `xprio` Set, is ALREADY EXECUTED and provides a complete four-plan template for exactly this shape of change, so this plan follows a proven path rather than inventing one. One measured fact reframes the item's stated benefit: NOTHING currently consumes backlog's `Kind` either (F5), so this plan delivers a recorded, validated field and must NOT claim it delivers cross-tree filtering.

## Goal

Let a work item's nature survive graduation. A bug filed in the backlog stays identifiable as a bug once it becomes a plan or a spec, using one shared vocabulary and the same recognized-but-optional mechanics the `Priority` field already established, so nothing existing is mass-failed and no second vocabulary appears.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared vocabulary, recognized in two contracts

- [ ] E-01 Export backlog's work-nature vocabulary as the ONE shared source and do not fork it. `backlog.KINDS` already exists as a frozenset of `bug`, `feature`, `chore`, `security`, `followup`. Consume THAT from the plan and spec contracts exactly as `backlog.PRIORITIES` is consumed today by `ipd_schema`, `specs`, `check_engine`, `releases`, and `research_cmd` (locate those consumers by grepping for `PRIORITIES` to copy the established import pattern). Do NOT define a second tuple, do NOT define a per-type subset, and do NOT rename `backlog.KINDS`. If the executor believes a shared SUPERSET is needed (see OQ-01's resolution, which rejects this), that is a scope question to report rather than a silent addition.
  - Depends on: none
  - Expected outcome: one vocabulary symbol is imported by every new consumer; a grep for the member tokens shows no second literal list; `backlog.KINDS` is unchanged.
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
| F7 | LOW | the item's design consideration 3 | Renaming backlog's `Kind` to `Work-Kind` would be a corpus-wide migration touching every existing backlog item plus its validator, its `new` verb, and its rendered template. The item calls the alternative "inconsistent" and prefers aligning everywhere; this plan declines the migration for this release and states the resulting asymmetry openly rather than pretending it is resolved. See OQ-03. | `backlog.py` reads/validates/renders `- Kind:` in its item parser, its checker, and its `new` renderer |
| F8 | MED | `tests/test_command_surface_declarations.py`; `agent_workflows/command_surface.py` | THE SCOPE-CHECK'S "CHECK THIS BEFORE STARTING" TASK IS NOW RESOLVED, so the executor does not have to discover it under time pressure, and the answer removes a scope risk rather than adding one. An OPTION does NOT trigger the undeclared-leaf requirement: `find_undeclared_leaves` compares parser LEAVES (subcommands) against `COMMAND_INVENTORY` and never inspects flags, so adding `--work-kind` to two existing verbs cannot create an undeclared leaf. Separately, `COMMAND_INVENTORY` does carry a per-command `legacy_flags` tuple, and the honest precedent is that `xprio` did NOT update it: `aw ipd set` and `aw specs set` both ACCEPT `--priority` today while neither declares it in `legacy_flags`. Nothing asserts that tuple is exhaustive (no test references `legacy_flags` except one `--json` membership check in `tests/conformance_matrix.py`), so omitting `--work-kind` there matches the sibling field exactly. CONCLUSION: `command_surface.py` stays OUT of scope, matching the fence as written. | measured at `770be84`: `find_undeclared_leaves` body compares `discover_parser_leaves(parser) - get_declared_leaves()`; `aw ipd set --help` lists `--priority` while `command_surface.py:714-723` omits it; `sed` of `specs set` `legacy_flags` yields 0 matches for priority; `grep -rn legacy_flags tests/` finds only `conformance_matrix.py:89` |
| F9 | MED | `tests/test_command_surface_declarations.py` | THE PRE-EXISTING FAILURE THE PLAN WARNS ABOUT IS REAL, MEASURED, AND ALREADY 59 STRONG, and it is INVISIBLE to the plan's own prescribed commands. `test_zero_undeclared_parser_leaves` fails with `59 != 0`, listing leaves such as `oc run`, `agy run`, `runs`, `commit`, `completion`, and `work begin`. Critically, the module is `pytestmark = pytest.mark.slow`, and this repo's addopts include `-m 'not slow'`, so the plan's prescribed bare `python3 -m pytest` NEVER RUNS IT and the executor would see a clean run while the conformance suite is red. It surfaces only under `-m ""` or `make test-all`. The plan already asks the executor to attribute pre-existing failures by name; this finding supplies the baseline so that attribution is checkable rather than a promise, and it means "the CLI-surface conformance tests must pass" was an unrunnable requirement as written. | measured at `770be84`: `python3 -m pytest tests/test_command_surface_declarations.py` reports `no tests ran`; with `-m ""` it reports `1 failed, 13 passed` and `AssertionError: 59 != 0`; `pytestmark = pytest.mark.slow` at `tests/test_command_surface_declarations.py:37`; `addopts = "-q -n auto --dist=worksteal -m 'not slow'"` at `pyproject.toml:122` |
| F10 | LOW | `aw ipd scaffold`; `.aw/records/specs/20260726-1340-01-ipd-spec.spec.md` | TWO MORE OF THE PLAN'S DEFERRED-TO-EXECUTOR CHECKS ARE RESOLVED HERE, both to "do nothing", which shrinks the change. First, E-04's conditional ("add to `aw ipd scaffold` if and only if `--priority` is already there"): `aw ipd scaffold --help` has NO `--priority`, so the condition is FALSE and `--work-kind` must NOT be added there. Second, the Spec/documentation-sync conditional (does `ipd-spec` enumerate recognized metadata fields, and was `Priority` added when `xprio` landed): `ipd-spec` contains ZERO occurrences of `Priority`, so it does not enumerate these optional fields and no spec edit is owed. Both answers preserve the plan's own instruction to follow the `Priority` precedent rather than invent an obligation. | measured at `770be84`: `aw ipd scaffold --help | grep -i priority` returns nothing (exit 1); `grep -c Priority .aw/records/specs/20260726-1340-01-ipd-spec.spec.md` returns 0 |

## Proposed changes (ordered, validatable)

1. Reuse `backlog.KINDS` as the one vocabulary (E-01).
2. Recognize `Work-Kind` in the IPD schema as optional, with no schema-level enum check (E-02).
3. Recognize `- Work-Kind:` on specs alongside the existing optional `Priority` (E-03).
4. Add `--work-kind` to the existing setters, mirroring `--priority` (E-04).
5. Register and implement `check.work-kind-invalid` following `check.priority-invalid` (E-05).
6. Prove it with tests mirroring the existing priority test modules (E-06).

## Deferred / out of scope (with reason)

- RENAMING backlog's own `Kind` to `Work-Kind` is deferred (OQ-03, F7). It is a corpus-wide migration and this plan is a release blocker; the honest cost is a naming asymmetry (backlog says `Kind`, plans and specs say `Work-Kind`) which the executor MUST record rather than gloss.
- ADDING `Work-Kind` to RESEARCH is out of scope. A research document's nature is already carried by its mandatory `.<kind>.md` document-type facet drawn from an 18-member vocabulary, so a second kind axis there would be genuinely confusing rather than merely redundant. The `xprio` Set did include research because priority is orthogonal to document type; work-nature is not.
- DERIVING the value from `From-Backlog` is deferred (OQ-02). Store explicitly for now.
- ATTENTION-BOARD wiring, labeling, and any sort-key change are out of scope. The `xprio` Set added labeling as its own deliberate step and explicitly left the sort key alone; per F5 nothing consumes a work-nature field today, so cross-tree FILTERING is a separate follow-up and this plan must not claim to deliver it. NOTE A DELIBERATE DIVERGENCE FROM THE PRECEDENT, recorded so a reviewer does not read it as an oversight: `xprio` child `1b45el` DID include `attention.py` in its scope and populated `Item.priority` as its E-04, whereas this plan excludes attention entirely. That is defensible, because `Item` already had a `priority` field to fill while it has no kind field at all, so wiring work-nature onto the board means ADDING a field and a render path, which is a larger change than the field this plan is asked to deliver. The consequence, which the executor must state rather than let a reader infer: after this plan, `Work-Kind` is recorded and validated but appears NOWHERE in `aw attention` output. The follow-up that adds board consumption is the same follow-up F5 names.
- Backfilling `Work-Kind` onto existing plans and specs is out of scope; absent means unclassified by design.

## Scope check

- Over-scope: none. `ipd_schema.py` carries E-02, `specs.py` carries E-03 and part of E-04, `check_engine.py` carries E-05, `cli.py` and `status_set.py` carry the setter wiring, and the test module is new. This mirrors the `Scope-Paths` the executed `xprio` children used for the same work.
- `agent_workflows/backlog.py` is deliberately NOT declared, which is the machine-readable expression of the OQ-03 deferral: E-01 only IMPORTS `backlog.KINDS` and must not modify it. If the executor finds itself editing `backlog.py`, the rename deferral has been breached and it must STOP and report. This is an IMPROVEMENT on the precedent rather than a deviation to correct: `xprio` child `1b45el` DID declare `backlog.py` for an import-only relationship and then had to reconcile it at finalize as "in-scope-unmodified ... import-only, not modified". Omitting a file you only import avoids that needless reconciliation ack, so keep it omitted; a reviewer comparing against the precedent should not ask for it back.
- Under-scope: NONE OUTSTANDING. The one item this section previously left for the executor to establish is now RESOLVED by measurement (F8): an OPTION cannot trigger the undeclared-leaf requirement, because `find_undeclared_leaves` compares parser LEAVES against `COMMAND_INVENTORY` and never inspects flags. The related `legacy_flags` tuple is not asserted exhaustive, and the `Priority` precedent left `--priority` undeclared on both `aw ipd set` and `aw specs set`, so `--work-kind` follows suit. `agent_workflows/command_surface.py` therefore stays OUT of scope and the fence is correct as written. If the executor nonetheless finds a NEW undeclared leaf appearing, that means a subcommand was added by mistake, so STOP and report rather than declaring the file.
- `cli.py` is one of the most contended files in this shared checkout and is the subject of pre-existing conformance failures. Re-read immediately before editing.

## Required tests / validation

- `tests/test_work_kind.py` must pass with every case in E-06. Falsifiability is specific: the absent-field cases must FAIL against an implementation that added the field to `META_REQUIRED`; the single-vocabulary assertion must FAIL against a forked literal list; the out-of-vocab case must FAIL against an implementation with no `aw check` rule.
- The EXISTING `tests/test_ipd_priority.py` and `tests/test_spec_priority.py` must pass UNCHANGED. They are the sibling feature's tests and touch the same schema and spec-contract code paths, so a regression there means E-02 or E-03 disturbed `Priority`. Neither file is in `Scope-Paths`.
- `aw check` must run clean on THIS repo's existing corpus after the change, which is the concrete proof of the no-mass-fail property: no existing plan or spec carries `Work-Kind`, so a correct optional implementation produces ZERO new findings. Paste the before and after counts.
- The CLI-surface conformance tests: `test_zero_undeclared_parser_leaves` is ALREADY FAILING with `59 != 0` at `770be84` (F9), so "must pass" is not achievable and is not this plan's job. The requirement is instead a NO-WORSENING one, and it must be measured deliberately because the module is marked `slow` and the fast suite SKIPS it entirely: run `python3 -m pytest tests/test_command_surface_declarations.py -m ""` before and after your change and paste both undeclared-leaf COUNTS. The count must not increase, and no leaf naming `work-kind` may appear. Per F8 an option cannot create a leaf, so an increase here means something unintended was added.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`. NOTE that the two invocations are NOT interchangeable for this plan: the bare run excludes `-m 'not slow'` content, which is exactly where the CLI-surface conformance module lives, so a clean bare run says NOTHING about it.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite during this sweep at `df731f1`: `2880 passed, 3 skipped, 4 xfailed`. Take your own before/after readings with their HEAD; concurrent agents are committing to `cli.py` and `check_engine.py`.
- End-to-end: set `Work-Kind` on a real plan and a real spec with the new setters, paste the resulting metadata lines, run `aw check` clean, then clear both with `--work-kind -` and show the lines are gone. Use artifacts you own or a fixture; do not modify another agent's in-flight plan.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- No spec text change is required. This plan adds an optional metadata field following an established, already-executed pattern and changes no contract that a spec pins.
- The `ipd-spec` document under `.aw/records/specs/` defines the IPD's structural contract including its metadata fields. This check is now DONE (F10): `.aw/records/specs/20260726-1340-01-ipd-spec.spec.md` contains ZERO occurrences of `Priority`, so it does not enumerate these recognized-but-optional fields and `xprio` added nothing there. Therefore make NO spec edit for `Work-Kind`. Do NOT invent a new documentation obligation, and do NOT edit a spec outside this plan's declared scope.
- Record in the terminal history that backlog keeps `Kind` while plans and specs gain `Work-Kind`, so the asymmetry is discoverable by whoever later decides on the rename (OQ-03).

## Open questions

### OQ-01: One shared vocabulary across all types, or a per-type appropriate set?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONE SHARED VOCABULARY, namely `backlog.KINDS` reused unchanged. The item raises a genuine tension, that a spec is rarely a "bug" and reads more like design or policy, and proposes a possible shared superset with per-type values. It is resolved against a superset for three evidenced reasons. First, the item's own stated risk is that "forcing one vocab creates the same drift we hit elsewhere", but the mechanism that actually produces drift in this codebase is FORKED definitions, which is why the executed `xprio` orchestrator's completion criteria demand "ONE shared PRIORITIES vocab consumed by all types (grep: no forked copies)". A per-type set is precisely such a fork. Second, adding members like `design` or `policy` for specs would immediately raise the question of whether a PLAN may use them, and the honest answer is yes, which makes the "per-type" framing collapse into a single superset anyway, at which point it is simpler to extend `backlog.KINDS` later if a real need appears. Third, the existing five members already cover the realistic spec cases adequately: a spec proposing new capability is `feature` and a spec codifying convention is `chore`. Accepted cost, to be recorded rather than hidden: `security` and `followup` will rarely apply to specs, and specs will cluster on `feature` and `chore`. If a genuine gap appears, the fix is ONE new member in the ONE shared set, in a follow-up.

### OQ-02: Store `Work-Kind` explicitly, or derive it from `From-Backlog`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: STORE EXPLICITLY; do not derive in this plan. Deriving is mechanically possible (F6: `From-Backlog` is already a recognized plan field and a shared resolver exists), and the item correctly notes derivation avoids two places to update. It is rejected here for reasons the repository makes concrete. A derived value would be UNDEFINED for the majority of artifacts, since most plans and specs carry no `From-Backlog` at all, so derivation cannot be the primary mechanism and would only ever be a fallback. A fallback also makes the field's value depend on ANOTHER artifact's current content, meaning a plan's work-nature could change silently when someone edits the source backlog item, which is exactly the kind of spooky action the explicit-metadata convention avoids. And an `explicit-overrides-derived` hybrid is the most complex of the three options while delivering the least certain benefit, so it is the wrong thing to build first. The forward-compatible note: because the field is OPTIONAL and absent means unclassified, a later derivation pass can populate absent values without contradicting anything this plan does.

### OQ-03: Rename backlog's `Kind` to `Work-Kind` for one cross-tree field name?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: DO NOT RENAME in this plan, and state the asymmetry openly. The item prefers "aligning on `Work-Kind` everywhere" and is right that two names for one concept is worse design. But the rename is a corpus-wide migration: `backlog.py` parses, validates, and RENDERS `- Kind:` in its item parser, its checker, and its `new` template, and every existing backlog item on disk carries the old spelling, so the change needs a migration plus a grandfathering window, which is a materially bigger and riskier change than adding an optional field. This item is a release blocker, and the blocking need is that a bug stays identifiable after graduation, which storing `Work-Kind` on plans and specs satisfies today. The mitigation that makes the asymmetry tolerable is that ONE vocabulary is shared (OQ-01), so the two field NAMES differ while the value space is identical and a mapping is trivial. This is a deliberate, recorded trade, and the executor MUST write it into the terminal history rather than implying the naming is uniform. The maintainer may prefer to do the rename first; that is a scheduling call, and its cost is delaying the blocker.

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
  - Required evidence: paste the new registry entry beside `check.priority-invalid` showing the same severity, assurance class, and determinism. Paste `aw check` flagging an out-of-vocab value on a PLAN and on a SPEC with rule `check.work-kind-invalid`. Paste `aw check` producing NO finding for a valid value and NO finding for an absent field. Then paste the whole-repo proof: `aw check` finding counts before and after the change on this repo's real corpus, showing ZERO new findings (the no-mass-fail property).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the full new module passing. Paste FALSIFIABILITY as actual failures: the absent-field cases failing when the field is made required, and the single-vocabulary assertion failing against a forked list. Paste `tests/test_ipd_priority.py` and `tests/test_spec_priority.py` passing UNCHANGED, since a break there means the sibling field was disturbed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, under the thresholds. Right-sizing checked per leaf: E-01 the shared vocabulary, E-02 the plan contract, E-03 the spec contract, E-04 the setters, E-05 the check rule, E-06 the tests. Each has its own falsifiable surface.

Open questions: ALL FOUR of the item's "resolve at plan time, do NOT assume" considerations are RESOLVED from repository evidence, so no maintainer decision is required to proceed. The maintainer should nonetheless know about TWO deliberate trades that are recorded rather than hidden. First, OQ-03 does NOT rename backlog's `Kind`, so after this plan backlog says `Kind` while plans and specs say `Work-Kind`, sharing one identical value space; if you would rather align the names first, that is a scheduling decision whose cost is delaying a release blocker. Second, and more important because it changes what this plan is worth: per F5 NOTHING consumes a work-nature field today, so this plan delivers a recorded and validated field, NOT the cross-tree "filter all bug work" capability the item's rationale describes. That capability needs a further change to the board and query surface, and the executor is forbidden from claiming it.

Scope fence: touch ONLY `agent_workflows/ipd_schema.py`, `agent_workflows/specs.py`, `agent_workflows/check_engine.py`, `agent_workflows/cli.py`, `agent_workflows/status_set.py`, and the new `tests/test_work_kind.py`. Do NOT touch `agent_workflows/backlog.py` (the OQ-03 rename deferral is expressed by its absence from scope; importing from it is fine, editing it is not), do NOT touch `agent_workflows/attention.py` or the sort key, do NOT add `Work-Kind` to research, do NOT edit `tests/test_ipd_priority.py` or `tests/test_spec_priority.py` (they must stay green unedited), and do NOT backfill the field onto existing artifacts. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured. Specifically for this plan: do NOT describe the outcome as enabling cross-tree filtering (F5).

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT with concurrent agents; `cli.py` and `check_engine.py` are both actively contended, so re-read them immediately before editing and locate insertion points by how `Priority` is wired rather than by line number. Line numbers are deliberately omitted from this plan.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
