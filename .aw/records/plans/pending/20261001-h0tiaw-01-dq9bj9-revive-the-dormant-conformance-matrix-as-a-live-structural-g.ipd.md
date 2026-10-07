# IPD: Revive the dormant conformance matrix as a live structural gate and retire its two stale exemptions

- Date: 2026-10-01
- Kind: child
- Concern: `tests/conformance_matrix.build_matrix` and `required_scenarios` compute a 1193-row coverage matrix over all 163 `COMMAND_INVENTORY` declarations and 152 parser leaves, AND NOTHING ASSERTS ANY OF IT. Measured in this lane at HEAD `b6792ad4a`, fourteen public names in that module (`SCENARIOS`, `required_scenarios`, `MatrixRow`, `MatrixReport`, `build_matrix`, `render_matrix_report`, `semantic_facts_from_human`, `outcome_family`, `ANSI_RE`, `GOLDEN_DIR`, `USAGE_ERROR_FLAG`, `RunResult`, `Exemption`, `_pinned_env`) have ZERO importers anywhere under `tests/`, `agent_workflows/`, `docs/` or `tools/`. The driver that executed them, `tests/test_cli_conformance_matrix.py`, was deleted by test-trimming commit `19313eed7`. THREE CONSEQUENCES ARE LIVE RIGHT NOW. (1) `agent_workflows/command_surface.py` reasons from `required_scenarios` in three separate comments, two asserting it is binding ("declaring the wrong class demands the wrong coverage"; "`status` obliges a `domain_failure` row while `next` does not. ... It must not be 'tidied' into symmetry") and the third correctly contradicting them ("`conformance_matrix` is currently a dead surface with no live importer (F-05), so the obligation is currently latent rather than enforced"), so the normative inventory documents two incompatible beliefs about its own gate. (2) `EXEMPTION_REGISTRY` carries THREE `known_broken` entries for `config show`, `config get` and `config is` citing backlog `dtq6jr`; that item is `done` and all three leaves now CONFORM (driven today: `config show --agent` emits a schema-valid `result` at exit 0 with exit parity, and `config get interactive --agent` / `config is interactive --agent` each emit a schema-valid `error` at exit 2 with exit parity), so the registry whose own banner reads "THE REGISTRY IS A CEILING, NOT A CONVENIENCE ... a `known_broken` entry REQUIRES a filed item id" is suppressing three passing leaves against a closed id. (3) `discover_parser_leaves`' own docstring says "``AliasEquivalenceTests`` owns alias behavior" and that class no longer exists, while twelve leaves are declared `command_class="alias"` and no surviving test asserts alias byte-equivalence.
- Scope: IN: restore the STRUCTURAL and ALIAS halves of the deleted driver as a new DEFAULT-COLLECTED test module, recovering them from `git show 19313eed7^:tests/test_cli_conformance_matrix.py` rather than rewriting from the docstring; re-pin its `declared_absent` assertion to the set measured at execution (EMPTY at review 2026-10-07, since both former members' owners `68sur3` and `lbbo9s` are `done`), citing the owner of any member that remains; delete the three stale `dtq6jr` exemptions and move the two argument-requiring config leaves into `RUNNABLE_ARGV` where they belong; resolve every remaining dead symbol in `tests/conformance_matrix.py` to either an executor or deletion, leaving no third category; and reconcile the three `command_surface.py` comments with what is then enforced. OUT: the expensive live scenario sweep and the vacuous human-banner parity gate (both carried by `2wowfy`); the renderer-level golden and budget gates (child `9i2hge`); fixing any leaf the re-measured pin names; adding any `LIVE_SAFE_LEAVES` member or any mutation-class coverage (plan `vfv2db`).
- Scope-Paths: tests/conformance_matrix.py, tests/test_conformance_matrix_structure.py, agent_workflows/command_surface.py
- Item-Dependencies: none
- Status: reviewed
- Work-Kind: chore
- Priority: low
- From-Backlog: h0tiaw
- Set: h0tiaw
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: dq9bj9

## Workflow history
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Re-measured at 20cec6d24: declared_absent is now empty (68sur3, lbbo9s done), so E-04 pins the execution-time set; alias pairs re-timed 11.8s/36.4s, now one parametrized case per pair; Exemption gained an importer via gm9baj; fixed probe 2; tied the alias class name to the discover_parser_leaves docstring; completed the execution contract.
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by 9i2hge E-06 (runs last) and the children's own V-items; coverage pass recorded
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: No orphaned golden and no orphaned symbol, checked across both children together

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `h0tiaw` as Order 01 of Set `h0tiaw` (orchestrator `l8wvv3`), which carries the Set-wide reasoning. Every claim here was MEASURED in this lane at HEAD `b6792ad4a`. The item's second open question ("whether the intended contract is still the one the helpers encode, since reviving a stale harness can assert obsolete promises") is answered per-assertion rather than wholesale, and it bites in exactly two places this plan handles explicitly: `test_declared_absent_leaves_are_only_the_known_prompts_family` pins a set that has GROWN from one member to two since the deletion, so a verbatim restore lands RED (E-03), and three `known_broken` exemptions now cite a `done` item while the leaves they exempt pass (E-02). The REST of the structural half is green and costs 0.513s, so the item's "low priority latent debt" framing is right about this child's urgency and wrong about its cost: this is cheap. One assertion is deliberately NOT restored verbatim and the reason is measured, not stylistic: the live scenario sweep costs several minutes and could only land `slow`, hence CI-advisory, which is why it is carried by `2wowfy` instead. `aw ipd lint --phase author` reports conforming.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the conformance matrix mean something again: one default-collected module that fails when a parser leaf
arrives undeclared, when a declared leaf loses a required scenario, when a THIRD declaration silently stops
having a parser leaf, or when an alias stops being byte-equivalent to its canonical target, with the
harness's exemption registry carrying no entry whose owner has closed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: recover the deleted driver and establish what it does today

- [ ] E-01 RECOVER THE DELETED DRIVER AND RUN IT UNCHANGED TO SEE WHAT BREAKS, before writing a single new
  assertion. Extract it with `git show 19313eed7^:tests/test_cli_conformance_matrix.py` into the worktree
  under its ORIGINAL name temporarily, run it, and CAPTURE THE RESULT PER TEST METHOD. This is the step that
  converts "revive a stale harness" from a guess into a measurement: the plan predicts exactly one
  structural failure (`test_declared_absent_leaves_are_only_the_known_prompts_family`, see F-02) and the
  prediction is falsifiable. RE-MEASURED AT REVIEW 2026-10-07 (HEAD `20cec6d24`): `build_matrix(_build_parser())`
  reports `declared_absent == []` and `undeclared == []` over 1209 rows, because `prompts set` was registered
  (commit `52ae65a96`) and the bare `upgrade-test` group was fixed (`lbbo9s` done via `7pnneh`). So the
  predicted failure is now `{"prompts set"}` expected versus `set()` actual, not the two-member set F-02 records.

  THE RECOVERED FILE CARRIES `pytestmark = pytest.mark.slow`, which is why running it needs `-m ''` or an
  explicit path plus `-m ''`. Note that marker: it is the thing E-04 removes for the structural half, and
  removing it is the whole point of this child (a `slow` test runs in CI only inside the step carrying
  `continue-on-error: true`, so it cannot fail a build).

  DO NOT KEEP THIS FILE. It is a measurement scaffold: it contains the live scenario sweep and the vacuous
  parity gate that this child deliberately does not revive. E-04 writes the surviving subset into a NEW
  module and this temporary file is deleted before any commit. If it is easier, extract it OUTSIDE the
  worktree, but do not leave an untracked copy behind, and do not commit it even transiently.
  - Depends on: none
  - Expected outcome: a per-test-method pass/fail table for the recovered driver, with
    `test_declared_absent_leaves_are_only_the_known_prompts_family` failing and its actual-versus-expected
    set captured verbatim (expected at review: actual `set()`), and an explicit statement of whether anything ELSE failed (which would be a
    finding this plan did not predict).
  - Execution state: pending

### Task group 2: correct the harness the restored gate will read

- [ ] E-02 DELETE THE THREE STALE `dtq6jr` EXEMPTIONS AND RELOCATE THE TWO THAT NEED ARGUMENTS. In
  `tests/conformance_matrix.EXEMPTION_REGISTRY`, the entries for `config show`, `config get` and `config is`
  all carry `reason_kind="known_broken"`, `citation="dtq6jr"` and the reason "Crashes with ImportError:
  cannot import name 'format_agent_json'". Backlog `dtq6jr` is `done`
  (`.aw/records/backlog/done/20260929-dtq6jr-01-dtq6jr-config-agent-importerror.backlog.md`) and the crash
  is gone.

  VERIFY BEFORE DELETING, because an exemption removed from a still-broken leaf turns
  `tests/test_agent_surface_conformance.py` red for someone else. Drive each of the three through
  `conformance_matrix.run_cli` with `--agent` and assert the four properties that test asserts (non-empty
  stdout, a terminal `result`/`summary`/`error` record, `agent_schema.validate_agent_record` returning `[]`,
  and record `exit` equal to the process returncode). Measured at authoring: `config show --agent` passes
  all four at exit 0. `config get --agent` and `config is --agent` with NO positional argument emit EMPTY
  stdout at exit 2 (argparse rejects before any handler runs), but WITH their required argument
  (`config get interactive`, `config is interactive`) both emit a schema-valid `error` record at exit 2 with
  exit parity. So `config show` needs no registry entry at all, and the other two need a `RUNNABLE_ARGV`
  entry supplying the argument, exactly as `RUNNABLE_ARGV` already does for `releases show`, `show`,
  `graduation` and eleven others.

  THE REGISTRY IS A CEILING. Do not add an entry to make anything pass. If a leaf measures non-conformant,
  that is a finding to report with its evidence and, if unowned, a filed carrier, not a new exemption.
  - Depends on: E-01
  - Expected outcome: three entries removed from `EXEMPTION_REGISTRY`, two entries added to `RUNNABLE_ARGV`
    with the argument each needs, `rg -n 'dtq6jr' tests/conformance_matrix.py` returning nothing, and
    `tests/test_agent_surface_conformance.py` still passing with its universe grown by three leaves.
  - Execution state: pending

- [ ] E-03 RESOLVE EVERY DEAD SYMBOL TO AN EXECUTOR OR TO DELETION, leaving no third category, and RECORD
  THE DECISION PER SYMBOL. The fourteen names with zero importers are `SCENARIOS`, `required_scenarios`,
  `MatrixRow`, `MatrixReport`, `build_matrix`, `render_matrix_report`, `semantic_facts_from_human`,
  `outcome_family`, `ANSI_RE`, `GOLDEN_DIR`, `USAGE_ERROR_FLAG`, `RunResult`, `Exemption` and `_pinned_env`.

  SIX ARE CLEARLY KEPT because E-04 executes them: `required_scenarios`, `build_matrix`, `MatrixRow`,
  `MatrixReport`, `ANSI_RE` and `USAGE_ERROR_FLAG`. FOUR ARE KEPT FOR A DIFFERENT REASON and the reason must
  be stated rather than assumed: `RunResult`, `Exemption` and `_pinned_env` are internal to `run_cli` and
  the registry, which DO have live importers, so they are not dead code at all and the sweep that listed
  them was counting IMPORTS, not USE; `GOLDEN_DIR` is read by sibling child `9i2hge`, so deleting it here
  would break that child. SAY SO EXPLICITLY, because a reader of this plan who deletes them on the strength
  of the word "dead" breaks two things.

  THREE ARE JUDGEMENT CALLS AND THIS ITEM OWNS THEM. `SCENARIOS` is a declared vocabulary that nothing
  reads: `required_scenarios` builds its own list literal and never consults the tuple, so the tuple is
  documentation that can drift from the function. Either make `required_scenarios` derive from it (so the two
  cannot disagree) or delete it. `semantic_facts_from_human` and `outcome_family` implement the parity
  predicate that F-03 measures as VACUOUS on all 16 curated leaves; either keep them with a non-vacuous
  executor (`runs query schema` DOES emit the required banner and would be one) or delete them and let
  carrier `2wowfy` reintroduce them with a working predicate. `render_matrix_report` renders a report nothing
  consumes; decide and say which.

  RE-MEASURED AT REVIEW: since authoring, executed plan `gm9baj` (commit `17801a40b`) added
  `UNREACHABLE_COMMAND_ALLOW_SET` to this module and made `tests/test_command_surface_declarations.py` import
  it together with `Exemption`, so `Exemption` now HAS a live importer. `UNREACHABLE_COMMAND_ALLOW_SET` is not
  one of the fourteen and is `gm9baj`'s, so leave it alone. ALSO CORRECT the `build_matrix` comment that reads
  "declared_absent is reported on MatrixReport but no longer asserted over", which E-04 makes false; name the
  new module instead.

  WHATEVER IS KEPT GETS AN EXECUTOR IN THIS CHILD. That is the invariant the backlog item asked for, and a
  symbol kept "for later" with a comment is the exact condition that produced the item.
  - Depends on: E-02
  - Expected outcome: a per-symbol table in the validation evidence reading KEPT-WITH-EXECUTOR (naming the
    test), KEPT-BECAUSE-INTERNAL (naming the live caller), or DELETED, covering all fourteen names with no
    omissions and no fourth category.
  - Execution state: pending

### Task group 3: land the gate, default-collected

- [ ] E-04 WRITE `tests/test_conformance_matrix_structure.py` CARRYING THE SURVIVING ASSERTIONS AND NO
  `slow` MARKER. Port from the recovered driver, keeping its four structural tests and its alias test, and
  dropping `LiveScenarioConformanceTests` and `FactParityTests` (carried by `2wowfy`).

  THE FOUR STRUCTURAL ASSERTIONS, each measured green at authoring: zero undeclared parser leaves
  (`find_undeclared_leaves(_build_parser())` returns `set()`); every declared leaf PRESENT in the parser has
  every scenario `required_scenarios` demands (measured: zero leaves missing any, across 1193 rows); the
  `declared_absent` set equals its PINNED membership; and every `LIVE_SAFE_LEAVES` member produces at least
  one matrix row.

  RE-PIN THE `declared_absent` ASSERTION TO THE SET MEASURED AT EXECUTION. The recovered assertion reads
  `assertEqual(set(report.declared_absent), {"prompts set"})`. At authoring the set was
  `{"prompts set", "upgrade-test"}`; RE-MEASURED AT REVIEW it is EMPTY, because both owners (`68sur3`,
  `lbbo9s`) are now `done`. So the expected pin is `set()`, and the assertion message must say what a
  non-empty value means: a declaration whose parser leaf vanished, to be fixed or owned with a filed id6,
  and cross-checked against the behavioral reachability gate
  `tests/test_command_surface_declarations.py::test_zero_unreachable_command_declarations` and its
  `UNREACHABLE_COMMAND_ALLOW_SET` (from `gm9baj`). If a member DOES exist at execution, pin it and name its
  live owner id6 in the message; never pin a member whose owner is closed. DO NOT delete the assertion and
  do not replace it with an inequality: its value is that a NEW silent absence fails. Fix no leaf here.

  KEEP THE ALIAS GATE, measured green: `spec check` versus `specs check` and `sanitize` versus
  `check-local-leaks` agree on returncode AND on stdout byte for byte. NAME THE CLASS `AliasEquivalenceTests`
  (or update `command_surface.discover_parser_leaves`' docstring in E-06), because that docstring justifies
  excluding aliases by citing a class of that name. PARAMETRIZE ONE TEST PER PAIR rather than looping
  subTests inside one function, so each pair gets its own hang budget. BUDGET IT HONESTLY: the two pairs
  cost 2.8s and 12.2s at authoring, but 11.8s and 36.4s RE-MEASURED AT REVIEW on a loaded machine, against
  the 90s `conftest.py` hang budget (`_DEFAULT_TEST_TIMEOUT = 90.0`). That fits, but it is the one assertion here with nontrivial cost;
  RE-MEASURE at execution and if the margin is under 3x, either narrow to the cheap pair with the cost
  recorded or set an explicit `@pytest.mark.timeout(<n>)` with the measurement justifying `<n>`. Do NOT
  reach for `slow` to make a timing problem go away: that moves the test into the CI-advisory step and
  forfeits the gate.

  NO CODE-PINNING (`GUIDING_PRINCIPLES` 16). Every assertion must come from building the real parser,
  building the real matrix, or running the real CLI. Do not read `agent_workflows/*.py` as text, do not
  assert a symbol exists, do not pin a docstring or a comment, and do not assert the ROW COUNT (1193 today)
  or the declaration count (163) as a census: those are the "no count or census pins" prohibition verbatim,
  and they would turn every legitimate new leaf into a failure. Assert the PROPERTY (no leaf lacks a
  required scenario), never the tally.
  - Depends on: E-03
  - Expected outcome: a new module that is COLLECTED AND PASSING under a bare `python3 -m pytest` with no
    `-m ''`, whose `declared_absent` assertion pins the execution-time set (expected `set()`) with a message
    naming the reachability gate and the owner of any member, whose alias test is one parametrized case per
    pair, and which contains no row
    count, no declaration count, and no `pytestmark = pytest.mark.slow`.
  - Execution state: pending

- [ ] E-05 PROVE THE GATE IS SENSITIVE BY BREAKING THE BEHAVIOR IT GUARDS, with THROWAWAY probes reverted
  before any commit. A restored gate that passes proves nothing about whether it can fail; `GUIDING_PRINCIPLES`
  16 states the bar directly ("A test is only valid if breaking the underlying behavior makes the test
  fail").

  THREE PROBES, EACH REVERTED. (1) Register a throwaway subparser leaf with no `CommandDeclaration` and
  confirm the undeclared-leaf assertion fails NAMING that leaf. (2) Change one declaration's
  `command_class` so `required_scenarios` demands a scenario the matrix does not supply, or add a throwaway
  declaration with no parser leaf, and confirm the coverage or `declared_absent` assertion fails naming it.
  (Removing a declaration whose leaf still exists trips the undeclared-leaf assertion, not `declared_absent`.)
  (3) Make one alias diverge from its canonical target (for example by having it emit one extra byte) and
  confirm the alias assertion fails on the byte comparison rather than passing on the returncode alone.

  PASTE EACH PROBE'S FAILURE OUTPUT and confirm `git status` is clean of the probes afterward. A probe left
  behind is a production edit this plan did not declare.
  - Depends on: E-04
  - Expected outcome: three pasted failures, each naming the specific thing broken, and a clean
    `git status --short` for `agent_workflows/` showing no probe survived.
  - Execution state: pending

### Task group 4: make the prose agree with the gate

- [ ] E-06 RECONCILE THE THREE `command_surface.py` COMMENTS THAT REASON FROM `required_scenarios`, which
  currently hold two incompatible beliefs. Two treat the obligation as binding: the `runs analyze`
  declaration comment ("`tests/conformance_matrix.required_scenarios` derives each leaf's REQUIRED scenario
  set from the `command_class` declared here ... declaring the wrong class demands the wrong coverage") and
  the `runs status` sibling-asymmetry comment ("`status` obliges a `domain_failure` row while `next` does
  not ... It must not be 'tidied' into symmetry"). The third, on `runs next`, states the opposite and is the
  one that is correct TODAY: "`conformance_matrix` is currently a dead surface with no live importer (F-05),
  so the obligation is currently latent rather than enforced, and 1 is still omitted on correctness grounds
  rather than because nothing would catch it."

  AFTER E-04 THE THIRD BECOMES FALSE AND THE FIRST TWO BECOME TRUE. Correct the third to say the obligation
  IS enforced, naming the module that enforces it, and PRESERVE its substantive point (that `1` is omitted
  from `runs next`'s `exit_contract` on correctness grounds, not for lack of a gate), because that reasoning
  is load-bearing and independent of whether a test exists. Leave the first two as found if they read true;
  if either overstates what E-04 actually enforces, narrow it. Also confirm the
  `discover_parser_leaves` docstring's `AliasEquivalenceTests` citation resolves to the E-04 class; if E-04
  named it differently, correct the docstring (docstring only).

  THIS IS A COMMENT EDIT IN A PRODUCTION MODULE AND NOTHING MORE. Change no `CommandDeclaration` field, no
  `exit_contract`, and no `command_class`: a declaration change would alter what the new gate demands, in
  the same commit that introduces the gate, making both unreviewable. The plan deliberately does NOT touch
  `CONTRIBUTING.md` step 6 either; that reconciliation belongs to sibling `9i2hge`, which lands the second
  half of the enforced set and so is the only child that can state the final answer promise-by-promise.
  - Depends on: E-05
  - Expected outcome: the `runs next` comment no longer claims a dead surface, naming
    `tests/test_conformance_matrix_structure.py` instead, with its `exit_contract` reasoning intact; a
    `git diff` on `agent_workflows/command_surface.py` showing comment lines only and no field change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- NO CODE-PINNING TESTS (`GUIDING_PRINCIPLES` 16, restated in `AGENTS.md`). The prohibitions that bite HERE
  specifically are "No count or census pins" (so no 1193-row or 163-declaration assertion) and "No
  production source inspection" (so the matrix must come from the real parser, never from reading
  `command_surface.py` as text). The affirmative duty is "Verify test sensitivity with mutation", which is
  why E-05 exists as its own item rather than as a line in E-04.
- DEFAULT COLLECTION IS THE WHOLE POINT. `pyproject.toml` `addopts` is
  `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` and `.github/workflows/tests.yml` runs
  `python -m pytest tests/ -n auto -rfEs` with no `-m ''`, while the `-m slow` step carries
  `continue-on-error: true`. So the recovered driver's `pytestmark = pytest.mark.slow` is not a detail to
  port faithfully; it is the defect to fix.
- THE PER-TEST HANG BUDGET IS 90s (`conftest.py` `_DEFAULT_TEST_TIMEOUT = 90.0`), overridable with
  `@pytest.mark.timeout(<seconds>)`. The alias gate's four subprocess invocations are the only part of this
  child that must be measured against it.
- `--dir`-STYLE FIXTURE SCOPING IS NOT AVAILABLE HERE, and that is why this child's cost is dominated by
  process spawns rather than tree walks. `conformance_matrix.run_cli` defaults `cwd` to `REPO_ROOT`; the
  alias pairs (`specs check`, `check-local-leaks`) legitimately read the live tree, which is also why their
  assertion compares the two surfaces to EACH OTHER rather than to any fixed output.
- THE BARE SUITE IS THE CONTRACT (`AGENTS.md`): run `python3 -m pytest` with no added flags, and
  specifically not `-n0`, not a second `-q`, and not `-p no:randomly`.

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | THE STRUCTURAL GATE IS GREEN AND COSTS 0.513s, so this is a cheap restoration and not a rescue. Driven in-process at HEAD `b6792ad4a`: `find_undeclared_leaves(_build_parser())` returns `set()`; `build_matrix` yields 1193 rows over 163 declarations and 152 parser leaves with `undeclared == []`; iterating every declaration present in the parser, ZERO have a `required_scenarios` member missing from their matrix rows. Import costs 0.669s and the whole structural pass 0.513s. | The matrix built, timed, and each assertion evaluated in-process. |
| F-02 | THE ONE ASSERTION THAT WOULD LAND RED IS `declared_absent`, AND BOTH OF ITS MEMBERS ARE FILED. The recovered `test_declared_absent_leaves_are_only_the_known_prompts_family` asserts `{"prompts set"}`; measured today `report.declared_absent` is `['prompts set', 'upgrade-test']`. `prompts set` is declared `command_class="mutation"` with `mutation_gate="auth_floor"` and has no parser leaf: open backlog `68sur3` ("prompts set dispatched but unregistered"). The bare `upgrade-test` group is declared `command_class="read"`, `agent_record_kind="result"` and is absent from `discover_parser_leaves` while its eight children (`upgrade-test list`, `env`, `probe`, `sandboxes`, ...) are all present; driven, `upgrade-test --agent` prints an argparse usage block on STDOUT and exits 2: open backlog `lbbo9s`, carrying `Blocks-Release: next`. So the fix is to widen the pin and cite both, which preserves the assertion's value (a third absence fails) without absorbing two bug fixes. SUPERSEDED AT REVIEW 2026-10-07: both owners are now `done` (`68sur3` via `gm9baj`/`52ae65a96`, `lbbo9s` via `7pnneh`), and `declared_absent` re-measured EMPTY; E-04 now pins the execution-time set. | `build_matrix` driven; `discover_parser_leaves` membership checked per command; both backlog records read; `upgrade-test --agent` driven. |
| F-03 | THE PARITY HELPERS ARE VACUOUS ON EVERY CURATED LEAF, which is why this child drops that gate rather than porting it. `semantic_facts_from_human` returns an outcome only when stdout line 1 starts with `AW ` and line 2 carries an uppercase status word from `_HUMAN_OUTCOME_WORDS`. Driven over all 16 `LIVE_SAFE_LEAVES`: ZERO satisfy that shape, so `outcome_family` is never compared and every subtest degrades to `assertEqual(agent.returncode, human.returncode)`. Three concrete shapes explain it: `status` opens `agent-workflows status`, `backlog check` opens `aw backlog check: all backlog items conform.`, and `layout` opens `AW Workspace Layout Model` whose second line is `INFO     Read-only inspection; nothing is written or moved.`. The helper is NOT broken: driven on a synthesized `CommandResult` render it correctly returns `{'outcome_family': 'findings'}`, and the live leaf `runs query schema` DOES banner (`AW runs query` then `✓ CONFORMS  schema: 10 views, 6 metrics`) but is not in the curated set. | All 16 leaves driven through the helper; 13 additional read/check leaves probed; the helper driven on a synthesized render. |
| F-04 | THREE EXEMPTIONS CITE A CLOSED ITEM AND ALL THREE LEAVES CONFORM. `EXEMPTION_REGISTRY` entries for `config show`, `config get` and `config is` carry `reason_kind="known_broken"` and `citation="dtq6jr"`; that item is in `.aw/records/backlog/done/`. Driving the four properties `tests/test_agent_surface_conformance.py` asserts: `config show --agent` gives non-empty stdout, a terminal `result` record, `validate_agent_record` returning `[]`, and `exit` 0 matching the returncode. `config get --agent` and `config is --agent` with no positional argument give EMPTY stdout at exit 2 (argparse rejects first), but `config get interactive --agent` and `config is interactive --agent` each give a schema-valid `error` record at exit 2 with exit parity. Both leaves declare a required positional (`config get`'s is `varname`), so they belong in `RUNNABLE_ARGV` alongside the fourteen entries already there. Re-driven at review 2026-10-07: same results (`config get interactive` gives `outcome: cannot-run`, `exit: 2`). A separate default-collected module, `tests/test_config_agent_surface.py`, already asserts all seven config verbs including these, which independently corroborates that the crash is gone. | All five invocations driven with records validated; `aw config get --help` read for the positional; `dtq6jr` located; `tests/test_config_agent_surface.py` read. |
| F-05 | THE ALIAS GATE HAS NO OTHER OWNER AND IS GREEN. Twelve declarations carry `command_class="alias"` (`attention`, `att`, `todo`, `sanitize`, `spec set`, `spec note`, `spec check`, `spec migrate`, `oc review`, `agy review`, `oc integrate`, `agy integrate`). Driven, both pairs the deleted `AliasEquivalenceTests` covered agree on returncode AND stdout byte for byte: `spec check` versus `specs check` (2.8s for the pair) and `sanitize` versus `check-local-leaks` (12.2s). `discover_parser_leaves`' docstring asserts "``AliasEquivalenceTests`` owns alias behavior" and explicitly relies on that ownership to justify excluding aliases from the leaf walk ("aliases must not appear here in the first place"), so the module's correctness argument cites a class that no longer exists. A grep for alias byte-equivalence across `tests/` finds no replacement. | Both pairs driven and byte-compared; the alias declarations enumerated; `discover_parser_leaves`' docstring read; `rg` for a replacement owner. |
| F-06 | THE "FOURTEEN DEAD SYMBOLS" COUNT IS AN IMPORT COUNT, NOT A USE COUNT, and conflating them would break two things. `RunResult`, `Exemption` and `_pinned_env` have zero IMPORTERS but are used INTERNALLY by `run_cli` and `EXEMPTION_REGISTRY`, which have three live importers between them, so they are not dead. `GOLDEN_DIR` has zero importers TODAY only because the module that read it (`test_cli_quality_gates.py`) was deleted; sibling child `9i2hge` restores that reader, so deleting it here would break that child. This is why E-03 demands a per-symbol verdict with a named reason rather than a bulk deletion. | The per-symbol `rg` sweep re-read against the module body; `9i2hge`'s scope read. |
| F-07 | THE SCENARIO VOCABULARY CAN ALREADY DRIFT FROM THE FUNCTION THAT IS SUPPOSED TO USE IT. `SCENARIOS` declares nine canonical scenario names as a tuple; `required_scenarios` builds `base = ["tty", "non_tty", "agent", "no_color", "help", "usage_error"]` as a fresh literal and appends `"json"`, `"domain_failure"` or `"success_preview"` conditionally, never consulting the tuple. So a typo in either is invisible to the other, and the tuple is a comment with syntax. That is a real (if small) defect in the harness itself and it is why E-03 requires a decision on `SCENARIOS` rather than a default keep. | Both definitions read; the literal confirmed as unreferenced to the tuple. |
| F-08 | ZERO-UNDECLARED-LEAVES IS ALREADY ASSERTED TWICE ELSEWHERE, so the restored module must add the coverage those do NOT. `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` and `tests/test_model_vocab.py::test_10_zero_undeclared_leaves` both assert `find_undeclared_leaves(...) == set()`, and both are default-collected. What neither asserts is the SCENARIO COVERAGE per declared leaf, the `declared_absent` pin, the `LIVE_SAFE_LEAVES`-produces-rows invariant, or alias byte-equivalence. Porting the undeclared-leaf test a THIRD time is permissible as the matrix's own precondition (`build_matrix` reports `undeclared` and the coverage assertion is meaningless if it is non-empty) but it must be stated as such rather than presented as new coverage. | Both existing tests read and confirmed default-collected (no `pytestmark`). |
| F-09 | NOTHING IN `.aw/records/specs/` SPECIFIES THIS HARNESS, so no spec amendment is owed. `rg` over the specs tree for `conformance_matrix`, `EXEMPTION_REGISTRY`, `LIVE_SAFE_LEAVES` and `conformance_goldens` returns no hits. The contract the harness MEASURES is `docs/cli-output-contract.md`, a normative document rather than a spec record, and this child changes none of it: every assertion restored here asserts behavior that document already describes and that the code already satisfies. | The `rg` sweep over `.aw/records/specs/`. |

## Proposed changes (ordered, validatable)

1. E-01 recovers the deleted driver from `19313eed7^`, runs it unchanged, and captures a per-method result
   table, confirming (or refuting) that exactly one structural assertion is now false.
2. E-02 deletes the three `dtq6jr` exemptions after re-verifying each leaf conforms, and adds the two
   argument-requiring config leaves to `RUNNABLE_ARGV`.
3. E-03 issues a per-symbol verdict over all fourteen zero-importer names: kept with a named executor, kept
   because internally used by a live caller, or deleted.
4. E-04 writes `tests/test_conformance_matrix_structure.py` with the four structural assertions plus the
   alias gate, no `slow` marker, no count pins, and a `declared_absent` pin re-measured at execution (expected empty).
5. E-05 proves the gate can fail, with three reverted throwaway probes and their failures pasted.
6. E-06 corrects the one `command_surface.py` comment that calls the harness a dead surface, preserving its
   independent `exit_contract` reasoning and changing no declaration field.

## Deferred / out of scope (with reason)

- THE LIVE SCENARIO SWEEP (`LiveScenarioConformanceTests`) and the HUMAN-BANNER PARITY GATE
  (`FactParityTests`). Deferred on measurement, not taste: the sweep costs several minutes and could only
  land `slow`, hence inside the CI step carrying `continue-on-error: true`, and the parity gate is vacuous on
  all 16 curated leaves (F-03). The orchestrator `l8wvv3` records the full timing table.
  - Carrier: 2wowfy
- THE RENDERER-LEVEL GATES (schema, ANSI, goldens, accessibility, truncation, budget) from the second
  deleted driver, plus the twelve unread `.golden` files and the one that has drifted. Sibling child, which
  is also why this child must not delete `GOLDEN_DIR` (F-06).
  - Carrier: 9i2hge
- FIXING ANY LEAF a re-measured `declared_absent` member names. At authoring these were `prompts set`
  (`68sur3`) and the bare `upgrade-test` group (`lbbo9s`, release-gated); both are `done` at review, so
  nothing is deferred today. A member found at execution is pinned with its live owner, not fixed here,
  because pulling a release-gated bug into a low-priority chore moves the gate onto the wrong artifact.
  - Carrier-Declined: no live member exists at review; any member found at execution is owned by the id6 E-04 cites.
- MUTATION-CLASS CONFORMANCE and any new `LIVE_SAFE_LEAVES` member. Declared scope of pending plan `vfv2db`
  (backlog `w78faq`), which measured eleven mutation leaves emitting human prose under `--agent` and declares
  `tests/conformance_matrix.py` in its own `- Scope-Paths:`. The semantic boundary: this child edits only
  `EXEMPTION_REGISTRY`, `RUNNABLE_ARGV`, the symbol set and the docstring, and adds no `LIVE_SAFE_LEAVES`
  member; `vfv2db` adds a mutation arm and an installed-project fixture. Neither needs the other's change.
  - Carrier: vfv2db
- `CONTRIBUTING.md` STEP 6, whose six promised live checks currently resolve to one. Reconciled by sibling
  `9i2hge` rather than here, because only the child that lands the SECOND half of the enforced set can state
  the final answer promise by promise; splitting the edit across two children would leave the file
  momentarily wrong in a new way.
  - Carrier: 9i2hge
- THE `SCENARIOS`-VERSUS-`required_scenarios` DRIFT RISK (F-07) IF E-03 CHOOSES DELETION. If E-03 instead
  wires the function to the tuple, the risk is closed and nothing is deferred.
  - Carrier-Declined: there is nothing to hand off under either branch. Deleting an unreferenced tuple
    removes the drift risk by removing one of the two things that could drift, and wiring it removes the risk
    directly; neither leaves a residue a future item would act on. E-03 records which branch it took.

## Scope check

- Over-scope: none. `tests/conformance_matrix.py` carries E-02's registry edits and E-03's symbol resolution
  plus the docstring correction its own text invites ("deciding whether to revive the remainder of the
  harness is tracked by open backlog item h0tiaw"). `tests/test_conformance_matrix_structure.py` is the new
  module from E-04. `agent_workflows/command_surface.py` carries E-06's comment-only edit. Deliberately NOT
  touched: `tests/test_agent_surface_conformance.py` (E-02 grows its universe through the registry, which is
  the designed mechanism, so the module itself needs no edit), `tests/test_exit_contract_conformance.py`
  (reads `LIVE_SAFE_LEAVES`, which this child does not change), `CONTRIBUTING.md` (sibling), and
  `tests/fixtures/conformance_goldens/` (sibling). No `.spec.md` file is declared, so a run must announce no
  declared spec edits and none may be made.
- Under-scope: two risks, both with a stated response. FIRST, E-02 may find a config leaf that does NOT
  conform, in which case the exemption cannot simply be deleted; the response is to re-file it against a
  LIVE owner with the measured evidence (never to leave a closed citation, and never to widen the reason to
  make it vacuous), and the entry then stays with a correct citation. SECOND, a concurrent lane may land a
  new leaf or a new declaration between authoring and execution, making the coverage or `declared_absent`
  assertion red on arrival. That is the gate working: measure the new member, find or file its owner, widen
  the pin with the citation. It is NOT grounds to relax the assertion, which `GUIDING_PRINCIPLES` 16's
  "Never weaken an assertion so it passes everywhere" forbids outright.

## Required tests / validation

- THE NEW MODULE `tests/test_conformance_matrix_structure.py`, COLLECTED AND PASSING under a bare
  `python3 -m pytest` with no `-m ''` override, asserting: zero undeclared parser leaves; no declared leaf
  present in the parser missing a `required_scenarios` member; `declared_absent` equal to the pinned
  execution-time set (expected `set()`) with the owner of any member in the failure message; every `LIVE_SAFE_LEAVES` member producing at
  least one matrix row; and both alias pairs byte-equivalent under `--agent`.
- THE SENSITIVITY PROBES of E-05: three throwaway breakages, each producing a NAMED failure, each reverted,
  with `git status --short` proving no probe survived.
- `tests/test_agent_surface_conformance.py` STILL PASSING after E-02 with its universe grown by the three
  un-exempted config leaves, which is the test that would go red if an exemption were removed prematurely.
- `tests/test_config_agent_surface.py` and `tests/test_command_surface_declarations.py` unchanged and
  passing, as the two independent corroborations that E-02's and E-04's premises hold.
- THE BARE FULL SUITE: `python3 -m pytest` with no added flags, at the base commit and again at the end, with
  the delta stated as a SET of test ids and required to be EMPTY. The bar is an empty delta, not a green run:
  a failure present before the change is not this plan's to fix.
- `aw ipd lint` conforming at `--phase author` before review and at `--phase pre-transition` before the
  terminal move, plus `aw check` reporting no new drift.

## Spec / documentation sync

No spec amendment, and no `.spec.md` path is declared in `- Scope-Paths:`, so a run executing this plan must
announce no declared spec edits and none may be made. Checked rather than assumed (F-09): `rg` over
`.aw/records/specs/` for `conformance_matrix`, `EXEMPTION_REGISTRY`, `LIVE_SAFE_LEAVES` and
`conformance_goldens` returns no hits, so no shipped spec specifies this harness. The contract it MEASURES is
`docs/cli-output-contract.md`, a normative document rather than a spec record; this plan changes none of it,
because every restored assertion asserts behavior that document already describes and that the code already
satisfies (F-01).

Two documentation touches, both deliberate and both narrow. The `tests/conformance_matrix.py` MODULE
DOCSTRING currently says "Former drivers (``test_cli_conformance_matrix.py`` and
``test_cli_quality_gates.py``) were removed by test-trimming commit 19313eed7; deciding whether to revive the
remainder of the harness is tracked by open backlog item h0tiaw", which this plan ANSWERS, so E-03 updates it
to name the modules that now consume the harness. The `agent_workflows/command_surface.py` comment calling
`conformance_matrix` "a dead surface with no live importer" becomes false the moment E-04 lands and is
corrected by E-06, preserving its independent `exit_contract` reasoning. `CONTRIBUTING.md` step 6 is
deliberately left to sibling `9i2hge` for the reason stated in the deferred section.

## Open questions

### OQ-01: Should the vacuous parity helpers be deleted or kept with a non-vacuous executor

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AS A BOUNDED CHOICE E-03 MAKES AT EXECUTION, with both branches
  acceptable and a third forbidden. The measurement (F-03) is settled: `semantic_facts_from_human` and
  `outcome_family` are reached by none of the 16 curated leaves, so porting `FactParityTests` as-is would add
  32 subprocess invocations asserting only the exit-code equality
  `test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership` already drives.
  BRANCH A, delete both helpers and let carrier `2wowfy` reintroduce them with a working predicate, is the
  cheaper branch and the one the plan expects. BRANCH B, keep them with a non-vacuous executor, is equally
  acceptable and has a concrete path: `runs query schema` DOES emit the required `AW runs query` banner, so a
  single-leaf parity assertion over a banner-emitting leaf would execute the helper for real. WHAT IS
  FORBIDDEN is the third option that created this backlog item: keeping them with no executor and a comment
  explaining why. E-03 records which branch it took and the evidence for it.

### OQ-02: Does the alias gate's 15s cost fit the default suite, or does it need a timeout override

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED WITH A RE-MEASUREMENT RULE RATHER THAN A FIXED ANSWER, because
  the number is machine-dependent and this plan must not hard-code a margin it measured once. Measured at
  authoring: the `spec check` pair costs 2.8s and the `sanitize` pair 12.2s, so roughly 15s of subprocess
  time against `conftest.py`'s 90s `_DEFAULT_TEST_TIMEOUT`, a 6x margin that fits comfortably. RE-MEASURED
  AT REVIEW on a loaded machine: 11.8s and 36.4s, so under 3x even per pair for `sanitize`, which is why E-04
  now parametrizes one test per pair and the rule below is expected to fire for the `sanitize` pair. E-04 RE-MEASURES
  at execution and applies one rule: if the margin is at or above 3x, land it unmarked with the measurement
  recorded; if below 3x, either narrow to the cheap pair (recording what coverage that forfeits) or set an
  explicit `@pytest.mark.timeout(<n>)` justified by the measurement, following
  `tests/test_exit_contract_conformance.py`'s precedent of `@pytest.mark.timeout(500)` for a measured 185s
  test. Reaching for `pytest.mark.slow` is NOT an option: it moves the test into the CI step carrying
  `continue-on-error: true`, which forfeits the gate and defeats this child's entire purpose.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the per-test-method result table from running the recovered driver, naming each
    of its test methods and its outcome. The table MUST show
    `test_declared_absent_leaves_are_only_the_known_prompts_family` FAILING, with its actual-versus-expected
    set quoted verbatim from the failure message. State explicitly whether any OTHER method failed; if one
    did, that is an unpredicted finding and must be described with its evidence before E-02 proceeds. PASTE
    `git status --short` showing the temporary recovered file is gone (or never entered the worktree).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE, for each of `config show --agent`, `config get interactive --agent` and
    `config is interactive --agent`, the actual stdout and exit code, plus the result of
    `agent_schema.validate_agent_record` on the terminal record (which must be `[]`) and the record's `exit`
    field alongside the process returncode. PASTE `rg -n 'dtq6jr' tests/conformance_matrix.py` returning
    NOTHING. PASTE the passing run of `tests/test_agent_surface_conformance.py` and state its universe size
    before and after (42 at authoring, 43 at review: re-derive), confirming the three leaves are now included rather than exempted.
    If any leaf measured non-conformant, PASTE that evidence and name the LIVE owner the entry was re-cited
    to.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE a table covering ALL FOURTEEN zero-importer names (`SCENARIOS`,
    `required_scenarios`, `MatrixRow`, `MatrixReport`, `build_matrix`, `render_matrix_report`,
    `semantic_facts_from_human`, `outcome_family`, `ANSI_RE`, `GOLDEN_DIR`, `USAGE_ERROR_FLAG`, `RunResult`,
    `Exemption`, `_pinned_env`) with a verdict of KEPT-WITH-EXECUTOR (naming the test method),
    KEPT-BECAUSE-INTERNAL (naming the live caller), or DELETED. No name may be omitted and no fourth verdict
    may appear. For `SCENARIOS` and for the two parity helpers, state which OQ-01 branch was taken and the
    evidence. PASTE the updated module docstring text showing it no longer describes the harness as awaiting
    a revival decision.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the output of `python3 -m pytest` (bare, no added flags) showing the new module
    COLLECTED AND PASSING, which is what proves default collection; a run that needed `-m ''` does not
    satisfy this item. PASTE `rg -n 'pytest.mark.slow|pytestmark' tests/test_conformance_matrix_structure.py`
    returning nothing. QUOTE the `declared_absent` assertion showing the pinned set (with `build_matrix(...).declared_absent`
    re-measured and pasted) and its message naming the reachability gate and the owner of any member. PASTE the measured wall time of the alias test and state the
    margin against the 90s budget, with the OQ-02 rule applied and the decision named. CONFIRM by quoting
    the relevant lines that the module contains no row count, no declaration count, and no read of any
    `agent_workflows/*.py` file as text.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE all three probe failures verbatim. Probe 1 must fail NAMING the throwaway
    undeclared leaf. Probe 2 must fail naming the specific leaf whose scenario coverage or declaration
    presence was broken (the throwaway declaration's name, for the `declared_absent` variant). Probe 3 must fail on the STDOUT byte comparison, not on the returncode, which is
    what proves the byte-equivalence half of the alias assertion is live rather than decorative. PASTE
    `git status --short` and `git diff --stat agent_workflows/` showing both empty of probe residue.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE `git diff agent_workflows/command_surface.py` in full, and confirm by reading it
    that EVERY changed line is a comment: no `CommandDeclaration` field, no `exit_contract` tuple, no
    `command_class` value may differ. QUOTE the corrected `runs next` comment showing it names
    `tests/test_conformance_matrix_structure.py` as the enforcing module and showing its original reasoning
    about `1` being omitted on correctness grounds is INTACT. State whether the other two comments were left
    as found or narrowed, with the reason, and quote the `discover_parser_leaves` docstring's alias-owner
    citation alongside the name of the E-04 alias class it now resolves to. PASTE the two bare-suite summary lines (base and final) and state
    the failure-set delta as a SET of test ids, which must be EMPTY.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires human approval before execution and carries no `- Readiness:` field, because that field is
an OUTPUT of `/plan-review` and writing one at authoring would forge the attestation the auto-approve
predicate reads first.

The executing agent commits ONLY the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never
`git add -A` and never pushing. Two commit-time hazards are specific to this plan. FIRST, E-01 brings a
recovered file into the tree temporarily; it must be gone before any commit, and `git diff --cached
--name-only` must be checked to confirm it is not staged. SECOND, E-05 edits production code as throwaway
probes; each must be reverted and the staged set re-verified, because a probe swept into a commit is a
production change this plan did not declare. Other agents may be working in this checkout concurrently, so any
uncommitted change to a path this plan does not own must be left alone.

SCOPE FENCE: `- Scope-Paths:` is a DECLARATION so finalize can reconcile edits; an out-of-scope edit the work
genuinely needs is made and then justified with `--scope-reason`, and a declared-but-unmodified path gets
`--scope-ack`. Paste ACTUAL runner output for every test claim; never claim a pass you did not run. Under `aw oc
run`/`aw agy run` the runner owns `aw ipd begin`/`finalize`; a hand executor runs `aw ipd finalize` itself,
never a hand `git mv`. Never push.

Do NOT move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports
conforming and every `V-*` above carries pasted evidence with `Result: pass`. The bar for V-06's suite delta
is an EMPTY SET, not a green run.
