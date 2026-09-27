# IPD: Make every graduation-source-link reader (From-Backlog and From-Spec) agree on the absent sentinels and flip the release-gates CI step to fail-closed

- Date: 2026-09-26
- Kind: child
- Concern: FOUR readers of a graduation-source link disagree about the literal values `-`, `none` and `unresolved`. `runner_shared._read_from_backlog` treats `{"-", "none", "unresolved"}` as ABSENT; `releases.check_from_backlog` (via `releases._ITEM_FROM_BACKLOG_RE`) reports each of them as `check.from-backlog-dangling`; `check_engine._META_FROM_BACKLOG_RE` (read by `find_from_backlog_plans`, `find_from_backlog_specs`, `_from_backlog_carrier_index`, the graduation index and the orphaned-blocker warning) indexes the literal as if it were an id6; and the SPEC-side twin `check_engine.check_from_spec_dangling` has the SAME defect on `- From-Spec:` (measured in review, F-7), which matters more because that rule already runs in the FAIL-CLOSED `aw check plans` CI step. The data finding that made this visible (an executed plan's `From-Backlog: none`) was removed by `dc1e791c`, and `aw check release-gates --agent` reports 0 findings at HEAD, but the code disagreement is live and the next hand-written sentinel re-reds the family. Separately, the CI `aw check release-gates` step is still advisory with a comment citing findings that no longer exist.
- Scope: IN: one schema constant naming the absent sentinels; all FOUR readers consult it (the three `From-Backlog` ones plus the `From-Spec` twin, which AGENTS.md calls "an equally valid gate carrier" and whose severity parity is stated in its own docstring); outcome tests for both fields; a regression guard proving no reader keeps a private sentinel set; flip the release-gates CI step to fail-closed and replace its stale comment. OUT: multi-valued `From-Backlog` (backlog 6os96s, which needs a single-vs-multi decision first); the setter `releases.set_from_backlog_line`; the SEPARATE fragility that a shipped-but-not-replaced planned release turns all 608 `Blocks-Release: next` records into `check.blocks-release-dangling` findings (F-8, carried by backlog item `cnn7au`; it is a property of the flip's operational cost, not of the sentinel disagreement).
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/runner_shared.py, tests/test_check_engine_release_gate.py, .github/workflows/tests.yml
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 7dcw6z
- Blocks-Release: next
- Set: frombacklog
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3cs7qg
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 all FIXED (fourth reader From-Spec added as E-04; release-transition cost disclosed; regression guard E-06; V-02 evidence command corrected)
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 7dcw6z: one sentinel set shared by all three From-Backlog readers, outcome tests, and the release-gates CI step flipped to fail-closed (0 findings at HEAD 61ef21d8).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every surface that reads a graduation-source link (`- From-Backlog:` and its `- From-Spec:` twin) gives the same answer for `-`, `none` and `unresolved` (absent, no finding, no carrier), one regression guard makes a future private sentinel set fail a test rather than a CI run, and the release-gate family becomes a fail-closed CI gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one sentinel set, four readers

- [ ] E-01 In `agent_workflows/ipd_schema.py`, directly below `META_FROM_BACKLOG`, add `SOURCE_LINK_ABSENT_SENTINELS: frozenset = frozenset({"-", "none", "unresolved"})` with a comment: these literal values mean "no source item" and every reader of a graduation-source link (`From-Backlog` AND `From-Spec`) treats them as if the field were absent; comparison is case-insensitive after stripping surrounding quotes. Add a helper `source_link_is_absent(value: str | None) -> bool` beside it (True for None, empty, or a sentinel), so readers share the comparison as well as the set. NAME IT FOR BOTH FIELDS, not `FROM_BACKLOG_*`: E-04 gives `From-Spec` the same treatment, and a `from_backlog`-named constant consulted by the spec reader is the kind of misnaming a later maintainer "corrects" by forking a second set.
  - Depends on: none
  - Expected outcome: one importable definition covering both link fields.
  - Execution state: pending

- [ ] E-02 Make the two SIMPLE `From-Backlog` readers use it. (a) `releases.check_from_backlog`: skip the match when the helper reports the captured value absent. `releases` imports `ipd_schema` nowhere today; use a module-scope `from agent_workflows import ipd_schema as _schema` (verified in review: `ipd_schema`'s module-scope import closure is `{artifact_core, attention_contract, backlog, config, lifecycle_dirs, plans, record_placement}` and does NOT contain `releases`, so there is no cycle; measured cost of adding it to a `releases`-only import is about 16ms of a roughly 110ms import, and every CLI path that reaches `check_from_backlog` already has `ipd_schema` in `sys.modules`, so the real added cost on those paths is zero). (b) `runner_shared._read_from_backlog`: replace the inline `raw in {"-", "none", "unresolved"}` with the helper. Do not change either regex's shape (that is 6os96s's decision).
  - Depends on: E-01
  - Expected outcome: a sentinel produces no dangling finding and the runner keeps returning None.
  - Execution state: pending

- [ ] E-03 Make the `check_engine` `From-Backlog` readers use it. Add a module-private `_from_backlog_value(text) -> str | None` that runs `_META_FROM_BACKLOG_RE.search` and returns None for an absent sentinel, and route every single-value call site through it (`find_from_backlog_plans`, `find_from_backlog_specs`, `_from_backlog_carrier_index`, and the plan-gate index in `release_gate_warnings`'s orphaned-live-blocker check); in `build_graduation_reverse_index`, which uses `_META_FROM_BACKLOG_RE.finditer`, filter sentinel values out of `sources`. `check_engine` already imports `ipd_schema as _S` at module scope, so no new import. Kept separate from E-02 because it is five call sites in one module with its own helper, which is what the `IPD-Z602` density advisory flagged on the authored single item.
  - Depends on: E-01
  - Expected outcome: a sentinel produces no carrier entry and no graduation edge.
  - Execution state: pending

- [ ] E-04 Make the SPEC-side twin agree. In `check_engine.check_from_spec_dangling`, skip the `_ITEM_FROM_SPEC_RE` match when the helper reports the captured value absent. THIS IS NOT SCOPE CREEP AND IT IS THE HIGHER-RISK HALF: measured in review, `- From-Spec: none` / `-` / `unresolved` each produce a `check.from-spec-dangling` finding, that rule is reachable from `aw check all` (not from `aw check plans`), and its own docstring states that severity parity between the two carriers of one handoff "is the point" because AGENTS.md makes a spec "an equally valid gate carrier". Leaving the twin disagreeing would ship the exact inconsistency this plan exists to remove, in the field with the identical contract. Leave that function's empty-known-set fail-safe guard untouched.
  - Depends on: E-01
  - Expected outcome: `- From-Spec:` and `- From-Backlog:` answer identically for all three sentinels.
  - Execution state: pending

- [ ] E-05 Add outcome tests to `tests/test_check_engine_release_gate.py`, reusing `_create_minimal_repo`: for each of `-`, `none`, `unresolved` (subTest), a plan with `- From-Backlog: <value>` yields 0 `check.from-backlog-dangling` from `check_engine.check_release_gates(repo)`, `check_engine.find_from_backlog_artifacts(repo, <value>)` returns empty, `check_engine._from_backlog_carrier_index(repo)` has no key for the sentinel, `check_engine.build_graduation_reverse_index(repo)` has no `('backlog', <value>)` key, and `runner_shared._read_from_backlog(<plan text>)` returns None. Same three sentinels on `- From-Spec:` yield 0 `check.from-spec-dangling` from `check_engine.check_from_spec_dangling(repo)` (the fixture needs a spec carrying an `- Id:` so the known-set guard does not short-circuit). Two NEGATIVE cases prove the change did not blunt the rules: a real-shaped but unknown id6 (`zz9zz9`) yields exactly 1 `check.from-backlog-dangling` and, on the spec field, exactly 1 `check.from-spec-dangling`. Outcomes only; no test reads source text or pins the constant's spelling.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: every sentinel case passes and each fails against its own pre-change reader; both negative cases still fire.
  - Execution state: pending

- [ ] E-06 Add the REGRESSION GUARD that makes the shared set durable, because nothing above stops the next reader keeping a private copy. Assert BEHAVIORALLY, not by reading source text: parameterize one test over the public readers that take a value or a repo (`runner_shared._read_from_backlog`, `check_engine.find_from_backlog_artifacts`, `check_engine._from_backlog_carrier_index`, `check_engine.build_graduation_reverse_index`, `releases.check_from_backlog`, `check_engine.check_from_spec_dangling`) and assert each treats EVERY member of `ipd_schema.SOURCE_LINK_ABSENT_SENTINELS` as absent, iterating the frozenset rather than a literal list. A sentinel added to the constant then automatically obliges every reader, and a reader that forked its own set fails here instead of reddening CI on live data.
  - Depends on: E-05
  - Expected outcome: adding a member to the constant fails the suite until every reader honors it.
  - Execution state: pending

### Task group 2: fail-closed CI gate

- [ ] E-07 In `.github/workflows/tests.yml`, first run `python -m agent_workflows check release-gates --agent` at the branch head and confirm `"findings":0` and exit 0 (measured in review at this branch head: `"outcome":"conforms","exit":0,...,"findings":0`; the authored plan cited HEAD `61ef21d8`, which is an ancestor, so RE-DERIVE it rather than trusting either number). Then change the step named `aw check release-gates (release-gate family; ADVISORY until baseline findings cleared)` to `aw check release-gates (release-gate family; fail closed)` with `run: python -m agent_workflows check release-gates --agent` (drop the `|| echo "::warning::..."` fallback), and replace the six-line comment above it (which cites `7l1ggb` and an executed plan's `From-Backlog: none`, neither of which is a finding any more) with a comment stating BOTH facts a future reader needs: that it joined the fail-closed set once the family reported zero findings (plan 3cs7qg), AND that the family includes `check.blocks-release-dangling`, so a release cycle that marks the single planned release `shipped` WITHOUT creating the next planned record turns every `Blocks-Release: next` record into a finding and reds `main` (measured in review: 608 findings in that state, 0 when a new planned record accompanies the ship; tracked by backlog item `cnn7au`, which the comment MUST name so a future reader meets the caveat where the gate lives). If the check reports ANY finding at the branch head, do not flip; see the stop condition.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the step fails the job on any release-gate finding, and its comment names the one operational state that reds it plus the item tracking its fix.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest`.
  - Depends on: E-06, E-07
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_schema.META_FROM_BACKLOG` is the field-name authority (runner_shared cites it, zhr6mc E-01); the sentinel set belongs beside it.
- `ipd_authoring` scaffolds `- Item-Dependencies: unresolved` and `- Work-Kind/Priority: unresolved`; `unresolved` is the toolkit's general "not yet decided" sentinel, which is why it belongs in the set. NOTE the scaffold NEVER writes `- From-Backlog: unresolved` (`ipd_authoring.build_skeleton` emits the line only `if from_backlog`), so every sentinel this plan handles arrives by HAND EDIT or by an external writer, which is exactly why a code-level agreement is the fix rather than a data cleanup.
- Tests assert OUTCOMES only (maintainer rule): no source-text or constant-spelling pins.
- `From-Backlog` and `From-Spec` are ONE contract with two carriers, stated in AGENTS.md ("a spec is an equally valid gate carrier") and restated in `check_from_spec_dangling`'s own docstring ("severity parity between the two carriers of one handoff is the point"). A change to the sentinel semantics of one is therefore a change to both, which is why E-04 exists (F-7).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `releases` imports `ipd_schema` NOWHERE today and `ipd_schema`'s module-scope closure does not include `releases`, so the import E-02 adds is acyclic (measured in review by AST walk).

## Findings

F-1..F-6 were measured by the author at HEAD `61ef21d8`. F-1..F-5 and F-7..F-9 were RE-MEASURED in review at this branch head (`61ef21d8` is an ancestor of it) by driving the shipped functions on a temporary fixture repo; every row below reports what the code actually did, not what its source reads like.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `releases.check_from_backlog` | Flags `-`, `none`, `unresolved` as dangling. | `m and m.group(1) not in known` with `_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^- From-Backlog:\s*(\S+)\s*$")`; driven on a fixture: 1 `check.from-backlog-dangling` for each of the three |
| F-2 | MED | `runner_shared._read_from_backlog` | Treats the same three as absent: the runner and the checker disagree. | `if not raw or raw in {"-", "none", "unresolved"}: return None`; driven: returns None for all three, `'zz9zz9'` for an unknown id6 |
| F-3 | LOW | `check_engine._META_FROM_BACKLOG_RE` consumers | A third reader with no sentinel handling at all; it indexes `none` as a carrier key. | `_META_FROM_BACKLOG_RE = _re.compile(r"(?m)^- From-Backlog:[ \t]*(\S+)[ \t]*$")`; driven: `_from_backlog_carrier_index` keys `['-']`/`['none']`/`['unresolved']` and `build_graduation_reverse_index` keys `('backlog','none')` etc. |
| F-4 | INFO | tree | 0 tracked records carry a sentinel today; the family is clean. | `grep -rn "^- From-Backlog: \(none\|-\|unresolved\)\s*$" .aw/records` -> 0 (exit 1); `python3 -m agent_workflows check release-gates --agent` -> `"findings":0`, exit 0 |
| F-5 | LOW | `.github/workflows/tests.yml` release-gates step | Still advisory, and its comment cites two findings that no longer exist. | comment names `7l1ggb` and "executed plan mjx7ne with From-Backlog: none"; `git show dc1e791c` removed that bullet from mjx7ne |
| F-6 | INFO | backlog 6os96s | Multi-valued `From-Backlog: a, b` is invisible to both anchored regexes. Same code, but NOT small: it first needs a single-valued-vs-multi-valued decision, and the only corpus instance (`nmlx47`) is now in `superseded/`. Not folded in. | 6os96s body; `.aw/records/plans/superseded/20260917-hostdedup-02-nmlx47-...ipd.md` `- From-Backlog: dstnso, 8hx3g3` |
| F-7 | MED | `check_engine.check_from_spec_dangling` | THE FOURTH READER, MISSED BY THE AUTHORED PLAN. `- From-Spec:` has the identical defect and the identical contract: a spec is "an equally valid gate carrier" per AGENTS.md and the function's own docstring says severity parity between the two carriers "is the point". Fixing only `From-Backlog` would ship the same inconsistency in the twin field. | Driven on a fixture: `From-Spec: -` / `none` / `unresolved` each -> 1 `check.from-spec-dangling`; `sss111` -> 0. Reachable from `aw check all` (`check_types` includes it) but NOT from `aw check plans`, so the fail-closed `check plans` CI step does not see it |
| F-8 | MED | `.github/workflows/tests.yml` release-gates step, after the flip | THE FLIP'S REAL OPERATIONAL COST IS NOT THE SENTINELS. `check.blocks-release-dangling` is a family member and `releases.resolve_release` maps `next` only when EXACTLY ONE release record is `planned`. So marking the single planned release `shipped` without creating the next planned record, or adding a second planned record, makes every `Blocks-Release: next` record dangle and reds `main` en masse. Fail-closed is still right (that state IS broken), but the flip must not be landed with this unstated. | Measured on a copy of `.aw/records`: baseline 0 findings; single planned release -> `shipped` = 608 `check.blocks-release-dangling`; two planned records = 608; shipped-plus-a-new-planned-record = 0. 608 records carry `Blocks-Release: next` (backlog 331, plans 269, specs 8) |
| F-9 | LOW | plan checklist as authored | No regression guard: E-01..E-03 made the readers agree TODAY, and nothing obliged the next reader (or a fourth sentinel) to honor the shared set, so the same divergence regrows silently. The `IPD-Z602` density advisory on the authored E-02 was the same structural signal (three readers in one item). | `aw ipd lint --phase author --detail` -> `advisory: IPD-Z602 (line 40): E-02: action text may bundle multiple concerns` |

## Proposed changes (ordered, validatable)

1. E-01: sentinel constant and helper, named for BOTH link fields.
2. E-02: the two simple `From-Backlog` readers (`releases`, `runner_shared`).
3. E-03: the `check_engine` `From-Backlog` readers (five call sites behind one helper).
4. E-04: the `From-Spec` twin (F-7).
5. E-05: outcome tests for both fields, with two negative cases.
6. E-06: the behavioral regression guard over the frozenset (F-9).
7. E-07: fail-closed CI step, with the F-8 operational state named in its comment.
8. E-08: bare suite.

## Deferred / out of scope (with reason)

- Multi-valued `From-Backlog` (F-6): needs a maintainer decision on the field's cardinality before either regex changes, and this plan must not diverge the two regexes.
  - Carrier: 6os96s
- The `Blocks-Release: next` release-transition fragility (F-8): a REAL gap and NOT this plan's defect. It is a property of `resolve_release`'s "exactly one planned record" rule meeting a fail-closed CI step, and fixing it means either a release-cycle obligation (ship and create the next record in one change) or a `next`-resolution change that touches every gate reader. Both need a maintainer decision this plan must not pre-empt. This plan's obligation is to STATE it in the CI comment (E-07) so the next release does not discover it from a red `main`. Not carried by 6os96s, which is about field cardinality.
  - Carrier: cnn7au

## Scope check

- Over-scope: none. The CI flip is in the backlog item's own resolution path (plan 2vw35i F-8 named this sentinel verdict as the blocker for the flip). E-04 (`From-Spec`) is IN scope rather than over: AGENTS.md and the function's own docstring make the two link fields one contract, so a sentinel semantics change to one that is not applied to the other is an incomplete fix, not a smaller one.
- Under-scope: closed by review. The authored plan covered three of four readers (F-7) and shipped no regression guard (F-9).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_check_engine_release_gate.py -v`.
- `python -m agent_workflows check release-gates --agent` before and after.
- Bare `python3 -m pytest`.
- Test rule: outcomes only.
- The two NEGATIVE cases in E-05 are load-bearing, not padding: the whole change makes a checker report LESS, so a test suite that only asserts silence would pass if a reader were broken into reporting nothing at all.

## Spec / documentation sync

No `.spec.md` defines the sentinel values of either link field, and none is amended here: AGENTS.md describes the fields and the dangling rules without listing sentinels, and this change makes every reader match the runner's already-shipped behavior. No `.spec.md` appears in `- Scope-Paths:` and none should.

ONE DOC LINE DOES GO STALE AND IT IS NOT IN SCOPE-PATHS. `AGENTS.md` states "In CI, `aw check release-gates` runs as a named advisory step in `tests.yml` until pre-existing baseline findings are resolved, and flips to fail-closed once clean." E-07 performs that flip, so the sentence becomes false the moment it lands. It sits in the repo-local `## Release gates (Blocks-Release)` section, BELOW the `<!-- /aw:block -->` marker (verified in review: the managed block ends before it), so editing it does not touch installer-managed text. Update that one sentence to read that the step IS fail-closed, add `AGENTS.md` to the edit, and JUSTIFY it at finalize with `--scope-reason AGENTS.md=...` rather than silently leaving the docs contradicting CI. Do not restate the F-8 operational caveat there; the CI comment is its home.

## Open questions

### OQ-01: Should `unresolved` count as absent, or as a finding (an undecided field on a plan)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Absent, matching the runner's shipped `_read_from_backlog`. `From-Backlog` is optional, so an undecided value carries no handoff claim; readiness of undecided fields is policed elsewhere (the approval floor refuses `unresolved` Priority/Work-Kind), not by the dangling-link rule.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c 'from agent_workflows import ipd_schema as s; print([s.source_link_is_absent(v) for v in (None, "", "-", "none", "NONE", "\"none\"", "unresolved", "abc123")])'` showing `[True, True, True, True, True, True, True, False]`; paste `python3 -c 'from agent_workflows import ipd_schema as s; print(sorted(s.SOURCE_LINK_ABSENT_SENTINELS))'` showing `['-', 'none', 'unresolved']`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `releases.check_from_backlog` and `runner_shared._read_from_backlog`; paste `grep -n '{"-", "none", "unresolved"}' agent_workflows/*.py` showing NO remaining inline sentinel set anywhere (measured before the change: exactly one hit, `runner_shared.py`). Do NOT use a bare `grep -n '"none"'` as the evidence: `runner_shared` legitimately contains unrelated `"none"` strings (`PEER_NONE`, `AUDIT_BASIS_NONE`, a `grandfathered`/`none` check, prompt text), so that command cannot distinguish success from failure. Also paste the acyclic-import proof: `python3 -c 'import agent_workflows.releases; print("ok")'` in a FRESH interpreter.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the five `check_engine` call sites plus `_from_backlog_value`; paste a driven probe on a temporary fixture repo showing, for each of `-`/`none`/`unresolved`, that `_from_backlog_carrier_index(repo)` has NO key for the sentinel and `build_graduation_reverse_index(repo)` has no `('backlog', <value>)` key, while a real id6 fixture still produces both.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `check_from_spec_dangling` diff; paste a driven probe showing `From-Spec: -`/`none`/`unresolved` each yield 0 `check.from-spec-dangling` and an unknown `zz9zz9` still yields exactly 1 (the fixture MUST contain a spec carrying an `- Id:`, or the empty-known-set guard returns 0 for every case and the test proves nothing).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_check_engine_release_gate.py -v` showing every new case passed; then revert ONLY the `releases.check_from_backlog` hunk IN THE WORKTREE and paste the three `From-Backlog` sentinel cases FAILING with a `check.from-backlog-dangling` finding (not an import error) while both negative cases still pass; revert ONLY the `check_from_spec_dangling` hunk and paste the three `From-Spec` sentinel cases FAILING the same way; restore both.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the guard test passing; then MUTATE it to prove it bites: temporarily add a fourth member to `ipd_schema.SOURCE_LINK_ABSENT_SENTINELS` (e.g. `"tbd"`) WITHOUT touching any reader and paste the guard FAILING and naming the readers that do not honor it; revert the mutation and paste it passing again. A guard that passes under that mutation has not proved the readers consult the shared set.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python -m agent_workflows check release-gates --agent; echo exit=$?` at the branch head showing `"findings":0` and `exit=0`; paste the `tests.yml` diff showing the `|| echo` fallback and the stale comment removed and the F-8 release-transition state named together with carrier item `cnn7au` (filed during review, already `open` and gated, so E-07 must CITE it and must not file a second one).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed; name any failure as pre-existing (with evidence at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. Two things, and the second is the consequential one.

FIRST, a behavior alignment with no data change: `aw check` stops flagging the three sentinel values the runner already ignores, on BOTH graduation-source link fields, and one test makes a future divergence fail the suite instead of CI. Nothing in `.aw/records/` is edited and 0 records carry a sentinel today, so this half changes no reported finding on this tree; it removes a trap the next hand edit would spring.

SECOND, the release-gate family becomes a FAIL-CLOSED CI step. After it, any `check.live-bug-ungated`, `check.from-backlog-dangling`, `check.from-backlog-gate-mismatch`, `check.blocking-item-closed-without-gate` or `check.blocks-release-dangling` finding FAILS the tests workflow on `main`. Two consequences are measured, not guessed, and a human should weigh them:

- Filing a live bug WITHOUT a gate reds CI. The documented `aw backlog new --work-kind bug --blocks-release -` path ("a default is not a prohibition; an author may legitimately file an ungated bug") produces exactly 1 `check.live-bug-ungated` finding, which after the flip blocks the merge. That is the intended policy ("we do not ship known bugs"), but it converts a documented escape hatch into a CI failure, and the human is the one to accept that.
- The release TRANSITION reds CI unless done in one change (F-8). `next` resolves only when exactly one release record is `planned`, so shipping the single planned release without creating its successor produces 608 `check.blocks-release-dangling` findings. Measured: 608 on ship-only, 608 on two-planned, 0 on ship-plus-new-planned. E-07 names this in the CI comment and backlog item `cnn7au` carries the fix; approving the flip is accepting that the next release must create the successor record in the same change.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above, PLUS `AGENTS.md` for the single stale CI sentence identified in the spec-sync section, which is deliberately left undeclared so the reconciliation records it explicitly. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if `aw check release-gates --agent` reports any finding at the branch head when E-07 runs, do NOT flip the step and do NOT edit another party's artifact to clear it; complete E-01..E-06, leave the step advisory with an updated comment naming the actual finding, mark E-07 not performed with that reason, and report. The sentinel work stands on its own and must still land.

RE-DERIVE, DO NOT TRUST, THE ZERO. Every finding count in this plan was measured before execution and the tree is shared. `"findings":0` is a LIVE ARTIFACT count, so E-07 re-runs the check at the branch head and reads its own output; the numbers in F-4 and F-8 are context for the reader, never the bar.

Commit ONLY paths in `- Scope-Paths:` (plus the justified `AGENTS.md` edit) through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `7dcw6z` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`, and the HANDOFF path was verified in review (`evaluate_blocking_close` returns `legitimate=True, path='HANDOFF'` for `7dcw6z` with this plan as the sole carrier), so the close is legitimate once the plan is executed. Backlog 6os96s stays open, and so does `cnn7au` (the F-8 carrier, filed during review): E-07 CITES it and must not file a duplicate.
