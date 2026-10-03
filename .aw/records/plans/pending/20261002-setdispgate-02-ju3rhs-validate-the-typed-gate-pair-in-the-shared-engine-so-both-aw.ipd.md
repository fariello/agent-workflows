# IPD: Validate the typed gate pair in the shared engine so both aw specs set spellings refuse an invalid Gate-Kind

- Date: 2026-10-02
- Kind: child
- Concern: A typed gate pair can be written to disk OUTSIDE its closed vocabulary, producing a record that violates the contract `AGENTS.md` states ("A `deferred` spec MUST carry a typed gate") and that the at-rest checker then reports as a finding. MEASURED 2026-10-02 at HEAD `45bd52b2f` over identical fixtures: `aw specs set <path> --status deferred --gate-kind bogus-kind --gate-ref x` exits 1 with `deferred requires a valid --gate-kind and --gate-ref` and leaves the spec byte-identical, while `aw specs set deferred abc123` with the SAME arguments exits 0, relocates the file to `specs/deferred/`, and writes `- Gate-Kind: bogus-kind`. The reproduction WIDENED the item in two ways it does not record. FIRST, the positional spelling also accepts a MALFORMED REF for a VALID kind (`--gate-kind date --gate-ref not-a-date` -> rc 0, written) and accepts NO GATE AT ALL (`aw specs set deferred abc123` with neither flag -> rc 0, a `deferred` spec carrying no gate whatsoever, which is the gate-missing violation rather than the gate-malformed one). SECOND, the BACKLOG twin is broken on BOTH of its spellings, not one: `aw backlog set <path> --status blocked --gate-kind bogus-kind --gate-ref x` ALSO exits 0 and writes the invalid kind, because `backlog.run_set` checks only that the pair is non-empty (`if not gk or not gr`) and never consults `GATE_KINDS`. Eight surfaces were enumerated and seven write an invalid gate. CAUSE, confirmed by reading the code: `specs.run_set` validates all four conditions (presence, `gk not in A.GATE_KINDS`, `A.validate_gate_ref(gk, gr)`, plus `--gate-summary` safety), while `status_set.apply_status_change`'s gate block writes on bare truthiness (`if gk and gr:`) and `status_set.validate_transition_allowed`'s backlog arm checks presence only. ROOT CAUSE is the dual dispatch fork `cli.main` creates by routing on whether `--status` was PASSED, the same fork as `h4fiwa` and backlog `fcnz1r`.
- Scope: IN: validate the typed gate pair ONCE, in a shared validator that every setter surface consumes, so all eight measured surfaces refuse identically on an out-of-vocabulary kind, a malformed ref, and a half-supplied pair; repair the two existing tests that pin the out-of-vocabulary kind `question` as acceptable; pin the parity as paired outcome tests across both record types and all four spellings each. OUT, each with a reason recorded under "Deferred": the `implementing -> implemented` evidence bypass (a separate measured defect with its own release-gated carrier and its own authored plan); removing the `cli.main` dispatch fork itself; changing the `GATE_KINDS` vocabulary or any per-kind ref regex; the `Release-Exempt-Kind` pair, which is already validated at the point of typing; and the three pre-existing suite failures this plan neither causes nor fixes.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/status_set.py, agent_workflows/backlog.py, agent_workflows/specs.py, tests/test_gate_pair_validation_parity.py, tests/test_backlog_gate_follows_status.py, tests/test_backlog_transition_gate.py, tests/test_blocks_release_reader_bounding.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: fv4b6s
- Blocks-Release: next
- Set: setdispgate
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: ju3rhs
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-03 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-measured the seven-of-eight bypass at lane HEAD f5671f1a2. Bounded the new refusal so same-status re-sets of an already-gated record without gate flags keep succeeding (measured regression under E-02 as written), corrected the stale fv4b6s status expectation, scoped the verb label in status_set, named the m1jlwm E-02 double-implementation hazard, and completed the execution contract.

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fv4b6s`. The item's measurement was re-reproduced at this tree's HEAD `45bd52b2f` rather than trusted, and the reproduction WIDENED it on two independent axes: the positional spelling also accepts a malformed ref and an absent gate (not only an invalid kind), and the BACKLOG twin is broken on BOTH spellings rather than one, so the defect is not purely a dispatch asymmetry. All eight setter surfaces were enumerated and measured. The fix's blast radius was measured by applying it in-memory and running nine candidate test modules, which identified exactly TWO breaking tests by name, both of which pin the out-of-vocabulary kind `question`; the FIRST such probe was a false negative because xdist made the monkeypatch inert, and that method defect is recorded as F-05 rather than quietly discarded. The bare-suite baseline was measured at the same HEAD. One adjacent defect found while measuring (the same vocabulary hole on `aw backlog new`) was FILED as release-gated backlog item `go8ztx` rather than absorbed into this plan or left as prose.
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a typed gate pair impossible to write outside its closed vocabulary, so that no `deferred` spec and
no `blocked` backlog item reaches disk carrying a `Gate-Kind` the contract does not define or a `Gate-Ref`
its kind's validator rejects, regardless of which verb, which spelling, or which `set` surface was used.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: one shared validator

- [x] E-01 Add ONE gate-pair validator that every setter surface will consume, returning an error string or `None` in the shape this repository already uses for a point-of-typing flag validator. It must enforce exactly the four conditions `specs.run_set` enforces today and NOT A FIFTH: both flags present together, `kind in attention_contract.GATE_KINDS`, `attention_contract.validate_gate_ref(kind, ref)`, and `attention_contract.is_safe_descriptive(summary)` when a summary is supplied.

    THE PRECEDENT FOR BOTH THE SHAPE AND THE HOME IS EXACT AND IN-TREE. `backlog.validate_release_exempt_flags` already does precisely this job for the SIBLING pair `Release-Exempt-Kind`/`Release-Exempt-Ref`: it takes a `verb` label plus the kind and ref, returns `Optional[str]`, checks both-or-neither, checks `kind not in A.GATE_KINDS`, checks `A.validate_gate_ref(kind, ref)`, and is consumed by more than one surface. Mirror that function's signature and its message style so the two read as a pair; a reviewer comparing them should see one pattern, not two.

    PUT IT IN `attention_contract`, NOT IN `specs` OR `backlog`. That module already OWNS this vocabulary: `GATE_KINDS`, `validate_gate_ref`, `is_safe_descriptive` and the three gate regexes are all defined there, and it is imported as `A` by every module that needs them. Siting the validator anywhere else forces a cross-import between two sibling record-type modules that have no reason to depend on each other, and `status_set` must reach it too. DO NOT create a new module for one function.

    TAKE THE VERB LABEL AS A PARAMETER so each caller's refusal names the command the operator actually typed (`aw specs set`, `aw backlog set`, `aw set`). NOTE THE LIMIT IN `status_set` (review PR-003): `validate_transition_allowed` does not know which of its five surfaces invoked it (it receives only the record, target, args and root, and the shipped exempt call passes the literal `"aw set"`), so pass `"aw set"` there too, as that precedent does, rather than inventing dispatch plumbing; the per-surface label is honest only for `backlog.run_set`. Do not let V-01's 'names the command typed' be read as requiring more. A single hardcoded prefix would make `aw backlog set` report itself as `aw specs set`, which is the exact class of misattribution that the sibling plan `c6f6sj` was authored to fix elsewhere in this same family; do not introduce a new instance of it while fixing a gate.

    THIS ITEM ADDS NO CALLER AND CHANGES NO BEHAVIOR. It is separated from E-02 and E-03 deliberately: the validator is shared by two record types through three call sites, and landing it alone makes the subsequent wiring a one-line change per surface that a reviewer can check against the single definition.
  - Depends on: none
  - Expected outcome: a new validator in `agent_workflows/attention_contract.py` that returns `None` for every valid pair and a verb-prefixed message naming the offending flag for an invalid kind, an invalid ref, and a half-supplied pair; called by nothing yet, so the suite's behavior is unchanged by this item alone.
  - Execution state: performed

- [x] E-02 Wire the validator into `status_set`, which is the shared engine that five of the eight measured surfaces reach: `aw specs set deferred <id6>`, `aw backlog set blocked <id6>`, `aw set <status> <id6>`, `aw set specs <status> <id6>`, and `aw set backlog <status> <id6>`. Refuse in `validate_transition_allowed`, not in `apply_status_change`.

    THE PLACEMENT IS THE LOAD-BEARING DECISION. `run_set_command` calls `validate_transition_allowed` in a PRE-FLIGHT loop over every matched record, BEFORE the dry-run branch and BEFORE `apply_status_change` writes anything, which is what makes a refusal leave the record byte-identical AND un-relocated. Refusing inside `apply_status_change` instead would refuse after a partially-applied batch, and relocation plus history-append happen on that path. Return `(False, <one-line reason>)` in the established shape; do not raise and do not print.

    GATE IT ON THE EXISTING `_GATE_STATUS_BY_TYPE` LOOKUP, NOT ON A HARDCODED `"deferred"`. That table already maps `specs -> deferred` and `backlog -> blocked` and is the single place this engine decides which status carries a gate for a given record type; reading it means the specs and backlog cases are fixed by ONE branch and a future gated record type is covered automatically. Fire only when `norm_status` equals that record type's gate status, so a transition OUT of the gated status still clears the fields as it does today.

    BOUND THE REFUSAL TO A TRANSITION INTO THE GATED STATUS, OR TO A PASSED FLAG, NEVER TO A SAME-STATUS RE-SET WITH NO GATE FLAGS (review PR-001). MEASURED at review over a fixture spec already `deferred` with a valid gate: today `aw specs set deferred <id6> --message note` and `aw set deferred <id6> --blocks-release next` both exit 0 and leave the existing gate untouched, because `apply_status_change` writes gate lines only `if gk and gr:`, so a same-status call with no flags PRESERVES the gate. A branch keyed only on `norm_status == gate_status` refuses both (patched and driven at review: both returned rc 1 "Refusing before making changes"), breaking every metadata-only re-set of a deferred spec or blocked item, which is exactly how `--blocks-release`, `--message` and similar same-status writes reach a gated record. So the predicate is: refuse when the record's CURRENT status differs from the gate status (a real transition in) and the pair is not valid, OR when EITHER `--gate-kind` or `--gate-ref` (or `--gate-summary`) was passed and the supplied pair is not valid. A same-status call that passes no gate flag keeps today's behavior and preserves the on-disk gate. This also corrects the pre-existing backlog arm, which refuses `aw backlog set blocked <id6> --message note` on an already-blocked item today (measured rc 1 "Moving backlog item to blocked requires --gate-kind and --gate-ref"); that change is intended, is the same parity, and E-05's same-status fence pins it.

    REPLACE THE PRESENCE-ONLY BACKLOG CHECK RATHER THAN STACKING A SECOND ONE BESIDE IT. `validate_transition_allowed` already contains a backlog-only arm refusing `blocked` when the pair is absent (`if not gk or not gr`). Leaving it in place beside the new branch would mean two refusals for the same condition with two different messages, decided by evaluation order. Delete it and let the shared validator own presence too, which is why E-01 requires the validator to check presence.

    DO NOT ALSO VALIDATE IN `apply_status_change`. A defensive second copy there is the duplication that caused this defect class, and `AGENTS.md` names fixing an instance by duplicating behavior into the second path as the reason instances keep being found.
  - Depends on: E-01
  - Expected outcome: all five `status_set`-reached surfaces exit nonzero on a transition INTO the gated status with an invalid kind, an invalid ref, or a half-supplied pair, and on any call that PASSES an invalid gate flag, leaving the record byte-identical and in its original status directory; a valid pair still succeeds and relocates; a same-status call with no gate flags on an already-gated record still succeeds and preserves its gate; a transition out of the gated status still clears the gate fields.
  - Execution state: performed

- [x] E-03 Wire the same validator into `backlog.run_set`, which serves the `aw backlog set <path> --status blocked` spelling and is the one surface this plan fixes that is NOT a dispatch asymmetry. MEASURED: this spelling exits 0 and writes `- Gate-Kind: bogus-kind`, so the backlog twin is broken on BOTH spellings and `fv4b6s`'s framing as a positional-only defect does not hold for backlog.

    REPLACE THE EXISTING PRESENCE-ONLY CHECK IN PLACE, WITH THE SAME SAME-STATUS BOUND AS E-02. Note that `run_set` today REWRITES the item from parsed fields, so on a same-status call it would drop the gate if no flags were passed; that is why it refuses today (measured: `aw backlog set <path> --status blocked --message n` on a blocked item -> rc 2). Keep that refusal for a same-status call without flags ONLY if preserving the on-disk gate would require a change outside this item; otherwise preserve the parsed `item.gate_kind`/`item.gate_ref` when the item is already blocked and no gate flag was passed, so the two spellings agree with E-02. Record which in the transition message. `run_set` already refuses with exit 2 when the pair is absent on a transition to `blocked`; swap that condition for the shared validator and keep the exit code 2 it returns today, since that is this verb's established refusal code for a bad flag and changing it would be an unrelated user-visible change.

    LEAVE `specs.run_set` ALONE except as E-04 requires. It already enforces all four conditions correctly, so rewriting it to call the shared validator is a refactor whose only user-visible effect would be changing a shipped refusal message. That trade is not worth taking inside a release-gated bug fix, and the duplication it leaves is a `chore` already carried elsewhere.

    DO NOT TOUCH `backlog.run_new`, WHICH IS A SEPARATE MEASURED DEFECT ALREADY FILED. `aw backlog new --status blocked --gate-kind bogus-kind --gate-ref x` also exits 0 and writes the invalid kind (measured; `aw backlog check` then reports `backlog.gate-kind-invalid`). It is the same vocabulary hole on a CREATE verb rather than a SET verb, it is not what `fv4b6s` filed, and folding it in would widen a fix whose blast radius is measured into one whose radius is not. It is carried by backlog item `go8ztx`, filed when this plan was authored.
  - Depends on: E-01
  - Expected outcome: `aw backlog set <path> --status blocked` with an invalid kind, an invalid ref, or a half-supplied pair exits 2 and leaves the item byte-identical in `open/`; a valid pair still succeeds and relocates to `blocked/`; `specs.run_set`'s refusal message is unchanged byte-for-byte.
  - Execution state: performed

### Task group 2: repair what the fix breaks

- [x] E-04 Repair the two tests that pin the out-of-vocabulary kind `question` as acceptable, both in `tests/test_backlog_gate_follows_status.py`: `TestBacklogGateFollowsStatus::test_route_e_transition_to_blocked_status_spelling` and `..._positional_spelling`. Each passes `--gate-kind question --gate-ref "Waiting on clarification"` and asserts rc 0.

    MEASURED, NOT PREDICTED, AND THIS IS THE WHOLE TEST-SIDE COST. The fix was applied in-memory to both `status_set.validate_transition_allowed` and `backlog.run_set`, then nine candidate modules were run with xdist disabled: `3 failed, 227 passed`, where the third failure is the pre-existing `test_every_real_spec_in_this_repository_still_conforms` (F-07). A sweep of every `--gate-kind` literal in `tests/` found `question` as the ONLY out-of-vocabulary value anywhere in the suite, with exactly those two uses.

    BEWARE THE INERT-PROBE TRAP, because this plan already fell into it once. The FIRST blast-radius probe monkeypatched the validator in the parent process and reported `173 passed`, i.e. a clean bill of health. That result was FALSE: `pyproject.toml` `addopts` supplies `-n auto`, and xdist workers are separate processes that never saw the patch. Any in-memory probe during execution MUST disable xdist (`-o addopts=""`) and MUST prove it fired, by counting invocations or by asserting a known-bad case now refuses. A probe that cannot show it fired is evidence of nothing.

    THE REPAIR IS TO MAKE THE FIXTURE'S GATE LEGITIMATE, NEVER TO WEAKEN THE VALIDATOR OR EXEMPT THE TEST. Substitute the in-vocabulary kind `external`, whose ref is a nonempty opaque string, so the existing ref `"Waiting on clarification"` stays valid unchanged (MEASURED: `validate_gate_ref("external", "Waiting on clarification")` is True, while the same ref under `question` is False). These tests' actual subject is that a transition into `blocked` DEFAULTS `- Blocks-Release:` on an ungated bug; the gate kind is incidental to it. Keep both the `- Blocks-Release: next` assertion and the `check_live_bug_gate(repo) == []` assertion intact, and keep both spellings' legs.

    A FIXTURE THAT NEEDS A GATE DISABLED IS TELLING YOU THE FIXTURE IS WRONG. Do not add a skip, do not widen `GATE_KINDS` to admit `question`, and do not route the test around the validator.
  - Depends on: E-02, E-03
  - Expected outcome: both tests pass with E-02 and E-03 applied, using `--gate-kind external` with their refs and assertions otherwise unchanged; no validator weakened, no vocabulary widened, no test skipped, and both spellings still covered.
  - Execution state: performed

### Task group 3: pin the parity

- [x] E-05 Author `tests/test_gate_pair_validation_parity.py` pinning the refusal on all EIGHT measured surfaces. Drive `cli.main` and assert on the exit code, the record's resulting LOCATION, and its resulting CONTENT. Pass `--no-commit` and `--yes` on every invocation. Model the helper shape on `tests/test_backlog_positional_close_gate.py` (one temp repo per case, `cli.main` under `redirect_stdout`/`redirect_stderr`), which is this repository's established template for a both-spellings property.

    THE EIGHT SURFACES, each measured in this plan's Findings: for specs, `aw specs set <path> --status deferred`, `aw specs set deferred <id6>`, `aw set deferred <id6>`, `aw set specs deferred <id6>`; for backlog, `aw backlog set <path> --status blocked`, `aw backlog set blocked <id6>`, `aw set blocked <id6>`, `aw set backlog blocked <id6>`. Seven of the eight write an invalid gate today, so seven of these cases FAIL at base and that is the point.

    COVER FOUR INPUT CASES ON EACH SURFACE: (a) an out-of-vocabulary kind refuses; (b) a valid kind with a malformed ref refuses (use `--gate-kind date --gate-ref not-a-date`, measured as accepted today by the positional spelling); (c) a half-supplied pair refuses, i.e. a kind with no ref and a ref with no kind; (d) a VALID pair still SUCCEEDS and relocates the record.

    CASE (d) IS NOT OPTIONAL AND IS THE SINGLE LIKELIEST WAY TO GET THIS WRONG. A "fix" that refuses every transition into the gated status would satisfy (a), (b) and (c) while breaking the verb entirely, and nothing else in this plan would catch it.

    ASSERT THE ABSENCE OF THE WRITE, NOT ONLY THE EXIT CODE. A test checking only a nonzero rc would pass against a half-fix that refuses AFTER relocating the file or AFTER appending a history record. Read the record back from its ORIGINAL path and assert byte-identical content and an unchanged status directory, and assert no file appeared in the destination directory.

    ADD THREE FENCES. The SAME-STATUS fence (review PR-001): on a record ALREADY in its gated status with a valid gate, a positional same-status call with NO gate flags (`aw specs set deferred <id6> --message note`, `aw set deferred <id6> --blocks-release next`, `aw backlog set blocked <id6> --message note`) SUCCEEDS and leaves the existing `- Gate-Kind:`/`- Gate-Ref:` lines intact, while the same call passing an INVALID `--gate-kind` refuses. The CLEARING fence: a transition OUT of the gated status (`deferred -> approved`, `blocked -> open`) still succeeds with no gate flags and still strips the gate fields, which is what bounds the new refusal to transitions INTO the gated status. The UNRELATED-TRANSITION fence: a non-gated transition (`draft -> to-review`) still succeeds with no gate flags.

    NO CODE-PINNING. Do not read production source with `inspect`, `ast`, regex or substring search, do not count callers, and do not assert docstring or comment text (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16).
  - Depends on: E-02, E-03
  - Expected outcome: a new module whose cases pass on all eight surfaces after E-02 and E-03, every refusal case asserting content and location as well as exit code, both fences present, and the pre-fix failure output pasted for the seven surfaces that are broken at base so the fix's effect is attributable.
  - Execution state: performed

### Task group 4: record the user-visible change

- [x] E-06 Add ONE `CHANGELOG.md` entry in the file's established voice describing the user-visible effect: `aw specs set`, `aw backlog set` and `aw set` now refuse a `Gate-Kind` outside the documented set or a `Gate-Ref` that does not match its kind, whichever spelling is used, instead of writing a record the checker later reports. Name the accepted kinds or point at where they are documented, since an operator hitting the new refusal needs to know what IS accepted.

    Name no private predicate and no internal function. Write no em or en dashes (user-facing prose, `AGENTS.md`).

    DO NOT CLOSE THE BACKLOG ITEM. `fv4b6s` carries `- Blocks-Release: next` and this plan is its `- From-Backlog:` carrier (MEASURED: no other artifact in the tree carries `- From-Backlog: fv4b6s`, so before this plan the release-gated item had NO carrier at all). The item is ALREADY `graduated` (set by the authoring run on 2026-10-02, measured at review), so nothing needs setting; the HANDOFF route makes the `done` close legitimate once this plan is `executed`, and an agent must never set it `done` by hand inside this plan.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: one CHANGELOG entry naming the refusal and the accepted vocabulary, containing no em or en dash; `fv4b6s` left untouched at its current `- Status:` (`graduated` at review, set by the authoring run) with `- Blocks-Release: next` intact.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE FORK IS ON `--status` PRESENCE, NOT ON ARGUMENT SHAPE. `cli.main`'s specs branch reads `if getattr(args, "status", None) is None:` and routes to `status_set.run_set_command(args.args, scoped_type="specs", ...)`, else sets `args.path` from `args.args[0]` and calls `specs.run_set(args)`. The backlog branch is byte-parallel, routing to `backlog.run_set`. Both spellings of each verb share ONE subparser, which is why `--gate-kind` is ACCEPTED by both while only one VALIDATES it.
- THE VOCABULARY HAS ONE OWNER. `attention_contract` defines `GATE_KINDS` (`artifact`, `decision`, `todo`, `issue`, `date`, `external`), the per-kind ref regexes, `validate_gate_ref` and `is_safe_descriptive`, and is imported as `A` wherever they are needed. A validator consuming them belongs there, beside them.
- THE SHAPE FOR A POINT-OF-TYPING FLAG VALIDATOR IS ALREADY SET. `backlog.validate_release_exempt_flags` takes a verb label plus a kind and ref, returns `Optional[str]`, and checks both-or-neither plus `GATE_KINDS` plus `validate_gate_ref` for the SIBLING `Release-Exempt-*` pair. This plan mirrors it rather than inventing a shape.
- THE PRE-FLIGHT IS WHERE A REFUSAL IS FREE. `status_set.run_set_command` calls `validate_transition_allowed` for every matched record before the dry-run branch and before any write, so a refusal there leaves the tree untouched; `apply_status_change` is past that point and performs the relocation and the history append.
- `_GATE_STATUS_BY_TYPE` IS THE SINGLE PLACE the shared engine decides which status carries a gate for a record type (`specs -> deferred`, `backlog -> blocked`). Reading it fixes both record types with one branch.
- OUTCOME TESTS ONLY (`AGENTS.md` execution contract; GUIDING_PRINCIPLES P16). A gate is verified by DRIVING the verb and reading the exit code plus the record on disk, never by asserting that a call to a predicate appears in the source.
- RUN THE SUITE BARE as `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted.
- XDIST MAKES AN IN-PROCESS MONKEYPATCH INERT. Workers are separate processes, so a patch applied in the parent is invisible to them and a probe reports a clean suite that proves nothing. This plan hit exactly that (F-05); any probe must pass `-o addopts=""` and demonstrate that it fired.
- `aw` re-execs into the outer checkout's package unless `AW_NO_REEXEC=1` is set; inside this lane it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence. The `aw` console script also does not export `AW_IPD_AUTHOR`, so `--author` must be passed explicitly to authoring verbs.
- A release-blocking backlog item is closed by the HANDOFF route when a `- From-Backlog:` carrier carrying the same gate reaches `executed`. This plan IS that carrier for `fv4b6s`, so it closes the gate by executing, not by calling a setter (E-06).

## Findings

Rows marked MEASURED were reproduced by driving the real surfaces through `cli.main` in scratch git repositories at this tree's HEAD `45bd52b2f`, with the fixture recreated fresh between every case.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (MEASURED) | Identical `approved` spec fixture, `--gate-kind bogus-kind --gate-ref x`. FLAG spelling `aw specs set <abs path> --status deferred` -> rc 1, stderr `aw specs set: deferred requires a valid --gate-kind and --gate-ref`, file byte-identical in `specs/approved/`. POSITIONAL spelling `aw specs set deferred abc123` -> rc 0, file relocated to `specs/deferred/` carrying `- Gate-Kind: bogus-kind` and `- Gate-Ref: x`. | **THE BACKLOG ITEM'S CORE CLAIM IS CONFIRMED EXACTLY.** One spelling of one verb refuses an out-of-vocabulary gate kind and the other writes it to disk. Note for a reviewer reproducing this: the FLAG spelling needs an ABSOLUTE path or one relative to the invoking cwd, not a path relative to `--dir`; a first attempt here passed a `--dir`-relative path and got rc 2 `cannot read`, which is a fixture error and not the defect. |
| F-02 | HIGH (MEASURED, WIDER THAN FILED) | Same fixture, POSITIONAL spelling. `--gate-kind date --gate-ref not-a-date` -> rc 0, written, `- Gate-Ref: not-a-date` on disk (`validate_gate_ref("date", ...)` requires `YYYY-MM-DD`). NO gate flags at all -> rc 0, file relocated to `specs/deferred/` carrying NO gate fields. The FLAG spelling refuses both, rc 1, byte-identical. | **THE HOLE IS THREE CONDITIONS WIDE, NOT ONE.** The item records only the invalid-KIND case. A malformed REF for a valid kind is equally accepted, and so is a `deferred` spec with NO typed gate whatsoever, which violates the same `AGENTS.md` sentence more directly than the filed case does. This is why E-01's validator must enforce presence, vocabulary and ref-shape together, and why E-05 tests all three per surface. |
| F-03 | HIGH (MEASURED, NOT IN THE ITEM, CHANGES THE DIAGNOSIS) | `blocked`-transition backlog fixture, `--gate-kind bogus-kind --gate-ref x`. FLAG spelling `aw backlog set <abs path> --status blocked` -> rc 0, item relocated to `backlog/blocked/` carrying `- Gate-Kind: bogus-kind`. POSITIONAL spelling -> rc 0, same result. `--gate-kind date --gate-ref nope` -> rc 0, written. | **THE BACKLOG TWIN IS BROKEN ON BOTH SPELLINGS, SO THIS IS NOT PURELY A DISPATCH ASYMMETRY.** `backlog.run_set` checks only `if not gk or not gr` and never consults `GATE_KINDS`, so unlike specs there is no correct path to copy from. A fix that only unioned the specs refusal across the fork would leave every backlog surface writing invalid gates. This finding is absent from `fv4b6s` and is why `agent_workflows/backlog.py` is in `Scope-Paths` and why E-03 exists. |
| F-04 | HIGH (MEASURED SURFACE INVENTORY) | All eight setter surfaces driven with `--gate-kind bogus-kind --gate-ref x`: `specs set --status` rc 1 (refused); `specs set <status>` rc 0 WROTE; `set <status>` rc 0 WROTE; `set specs <status>` rc 0 WROTE; `backlog set --status` rc 0 WROTE; `backlog set <status>` rc 0 WROTE; `set <status>` (backlog) rc 0 WROTE; `set backlog <status>` rc 0 WROTE. | **SEVEN OF EIGHT SURFACES WRITE AN INVALID GATE; EXACTLY ONE REFUSES.** Five of the seven reach `status_set` and are fixed by E-02's single branch; two reach `backlog.run_set` and are fixed by E-03. This inventory is what makes E-05's eight-surface matrix a measured requirement rather than defensive over-testing, and it is why the fix is sited in the shared engine instead of patched per spelling. |
| F-05 | HIGH (METHOD DEFECT FOUND IN THIS PLAN'S OWN WORK) | Probe 1 monkeypatched `status_set.validate_transition_allowed` in the parent process and ran six modules under default `addopts`: `173 passed`, no failures. Probe 2 applied the same patch, added an invocation counter, and ran with `-o addopts=""`: `1 failed, 110 passed`, counter `calls=120 new_refusals=1`. | **THE FIRST BLAST-RADIUS MEASUREMENT WAS A FALSE NEGATIVE AND IS RECORDED AS SUCH.** `addopts` supplies `-n auto`, so xdist workers are separate processes that never saw the patch; the clean result proved only that the unpatched code still passes. Had it been trusted, this plan would have claimed zero test-side cost and the executor would have been ambushed by two failures. Any probe run during execution must disable xdist AND prove it fired. |
| F-06 | HIGH (MEASURED BLAST RADIUS, AFTER F-05's CORRECTION) | Probe 3 patched BOTH `status_set.validate_transition_allowed` and `backlog.run_set`, ran nine specs/status/backlog modules with `-o addopts=""`: `3 failed, 227 passed`, `new_refusals=2`. The three: `test_backlog_gate_follows_status.py::TestBacklogGateFollowsStatus::test_route_e_transition_to_blocked_status_spelling`, `..._positional_spelling`, and the pre-existing `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` (F-07). A regex sweep of every `--gate-kind` literal in `tests/` found exactly ONE out-of-vocabulary value, `question`, with exactly those two uses. | **THE TEST-SIDE COST IS EXACTLY TWO TESTS, BOTH FOR THE SAME REASON, AND THEY ARE NAMED.** Both pin `--gate-kind question`, which is not in `GATE_KINDS`, as acceptable. The sweep bounds the cost: no other test anywhere in the suite passes an out-of-vocabulary kind. `validate_gate_ref("external", "Waiting on clarification")` is True while the same ref under `question` is False, so E-04's substitution needs no change to the refs or the assertions. |
| F-07 | N/A (BASELINE) | Bare `python3 -m pytest` at HEAD `45bd52b2f`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 259.52s`. The three: `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, `test_selector_type_containment.py::test_must_not_refuse_matrix`. Each is already filed (`6bolin`, `8jeh4x`, `bxnhdj`). | **THE BASE IS NOT GREEN, SO THE BAR IS AN UNCHANGED FAILURE SET BY NAME, NEVER A COUNT.** Re-derive the baseline before editing and compare SETS BY NAME: a count comparison would hide a real regression behind a concurrently-fixed failure. The first of the three asserts a whole-corpus property over the LIVE `.aw/records/` tree, so another party's artifact can change its result between runs. Do not fix another item's failure here. |
| F-08 | MEDIUM (MEASURED, DELIBERATELY OUT OF SCOPE) | `aw backlog new --summary ... --status blocked --gate-kind bogus-kind --gate-ref x --apply` -> rc 0, wrote `backlog/blocked/<...>.backlog.md` carrying `- Gate-Kind: bogus-kind`. `aw backlog check` on the result -> rc 1, `backlog.gate-kind-invalid: Gate-Kind not in ['artifact', 'date', 'decision', 'external', 'issue', 'todo']`. | **THE SAME VOCABULARY HOLE EXISTS ON THE CREATE VERB, AND IS NOT FIXED HERE.** `backlog.run_new` checks only `if status == "blocked" and (not item.gate_kind or not item.gate_ref)`. It is a different verb from the one `fv4b6s` filed, folding it in would widen a fix whose blast radius is measured into one whose radius is not, and the checker arm quoted here is the proof that the at-rest validator catches what the write path lets through. FILED as its own release-gated item `go8ztx` at this plan's authoring time, carrying this measurement verbatim. |
| F-09 | LOW (SCOPE FENCE, MEASURED) | The at-rest validators already enforce the full contract: `specs.validate_spec` emits `attention.gate-missing` / `attention.gate-malformed`, and `backlog.validate_item` emits `backlog.gate-missing` / `backlog.gate-kind-invalid` / `backlog.gate-ref-invalid`. `specs.run_set` re-runs `validate_spec` in memory and refuses a nonconforming result. | **THE CONTRACT IS ALREADY CORRECT AT REST; ONLY THE WRITE PATHS ARE BEHIND IT.** So this plan changes no rule and amends no spec: it moves an existing refusal earlier, from after-the-fact finding to fail-closed. It also explains the second-order effect `fv4b6s` records, since the checker is what eventually catches these records, and the window between the write and the check is however long before anyone runs it. |
| F-10 | LOW (CARRIER STATE, MEASURED) | `grep -rn "From-Backlog: fv4b6s" .aw/records/` returns nothing at this HEAD. Pending plan `m1jlwm` (Set `setdisp`, Order 3) proposes fixing this bypass and `h4fiwa`'s together, but declares `- From-Backlog: fcnz1r` and depends on `executed:afdmn6`, which itself depends on `executed:c6f6sj`. | **THE RELEASE-GATED ITEM HAD NO CARRIER BEFORE THIS PLAN.** So authoring this plan is what makes `fv4b6s`'s gate closable. This plan is deliberately INDEPENDENT (`- Item-Dependencies: none`) rather than slotted behind that two-plan chain, so a release blocker is not held hostage to a `chore`-classified refactor Set. If a maintainer prefers the Set to own it, retire THIS plan to `superseded/` and add `- From-Backlog: fv4b6s` plus the gate to `m1jlwm`; do not simply delete this plan, which would return the item to having no carrier. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/attention_contract.py`: one shared gate-pair validator beside the vocabulary it consumes, mirroring `backlog.validate_release_exempt_flags`'s signature and message style (E-01).
2. `agent_workflows/status_set.py`: `validate_transition_allowed` consumes that validator under the existing `_GATE_STATUS_BY_TYPE` lookup, and the presence-only backlog arm is replaced rather than stacked beside it, so all five shared-engine surfaces refuse in the pre-flight before any write (E-02).
3. `agent_workflows/backlog.py`: `run_set`'s presence-only `blocked` check is replaced by the shared validator at the same exit code, closing the two surfaces that are not dispatch asymmetries (E-03).
4. `tests/test_backlog_gate_follows_status.py`: the two fixtures pinning `--gate-kind question` are repaired to the in-vocabulary `external`, refs and assertions unchanged (E-04).
5. `tests/test_gate_pair_validation_parity.py`: new eight-surface outcome tests covering invalid kind, invalid ref, half-supplied pair, and the valid-pair success case, plus a clearing fence and an unrelated-transition fence (E-05).
6. `CHANGELOG.md`: one entry naming the refusal and the accepted vocabulary (E-06).

`agent_workflows/specs.py` is declared in `Scope-Paths` because E-01 adds the shared validator that
`specs.run_set`'s own four-condition check is the model for, and E-03 requires confirming that file's
refusal message is unchanged byte-for-byte; if the executor finds `specs.run_set` must change to keep
that message identical, that change is authorized and must be recorded in the transition message.

## Deferred / out of scope (with reason)

- THE `implementing -> implemented` EVIDENCE BYPASS IS NOT FIXED HERE. The positional `aw specs set implemented <id6>` succeeds with no `--evidence` while the `--status` spelling refuses. It is a genuinely separate defect in a different code path (the transition-authority check rather than the gate-write path), it has its own measurement and its own release-gated carrier, and a plan authored for it already exists in this same Set at Order 1. Folding it in would merge two independently reviewable release blockers.
  - Carrier: h4fiwa
- THE DISPATCH FORK ITSELF IS NOT REMOVED. `cli.main` still routes on `--status` presence and both engines still exist. This plan installs ONE validator both sides consume rather than removing the fork, deliberately: this bug is release-gated and must be able to ship now, while removing the fork is a larger behavior-preserving migration gated on a maintainer decision. Shipping the gate fix behind that decision would hold a release blocker hostage to a design question. That durable fix is the root-cause remedy and is why this class has recurred.
  - Carrier: fcnz1r
- `aw backlog new --status blocked` IS NOT FIXED HERE (F-08). It writes an out-of-vocabulary kind too, but it is a CREATE verb rather than a SET verb, it is not what `fv4b6s` filed, and its blast radius was not measured by this plan's probes. It should consume the same E-01 validator, which is a one-line change once that validator exists, so this is sequencing rather than a design question. FILED AT AUTHORING TIME, not left as a note: the item carries F-08's measurement verbatim and names E-01's validator as the fix, so the follow-up needs no re-discovery.
  - Carrier: go8ztx
- THE `GATE_KINDS` VOCABULARY AND THE PER-KIND REF REGEXES ARE NOT CHANGED. Widening or narrowing what counts as a valid gate is a contract change deserving its own review, and the vocabulary is correct as documented in `.aw/records/backlog/README.md`, `.aw/records/specs/README.md` and the implemented attention spec. In particular `question` is NOT added to admit E-04's two fixtures; the fixtures are repaired instead.
  - Carrier-Declined: There is nothing durable to carry. No defect was found in the vocabulary or in any ref validator; the only finding was two tests using a kind that was never valid, which E-04 fixes in this same change. A carrier would track work that does not exist.
- `specs.run_set` IS NOT REFACTORED ONTO THE SHARED VALIDATOR. It already enforces all four conditions correctly, so the only user-visible effect of rewriting it would be changing a shipped refusal message as collateral of a refactor, inside a release-gated bug fix. The residual duplication is a `chore`, not a defect.
  - Carrier: fcnz1r
- THE `Release-Exempt-Kind`/`Release-Exempt-Ref` PAIR IS NOT TOUCHED. It is already validated at the point of typing by `backlog.validate_release_exempt_flags` on every surface, which is precisely why that function is E-01's model rather than its target.
  - Carrier-Declined: Nothing is wrong with it, so there is nothing to carry. It is cited here only as the shape precedent.
- THE THREE PRE-EXISTING SUITE FAILURES (F-07) ARE NEITHER CAUSED NOR FIXED HERE. Each already has its own backlog item. Fixing another item's failure inside this plan would make this plan's own regression evidence unattributable, which is exactly what the compare-sets-by-name rule protects.
  - Carrier: 6bolin

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is edited by a numbered E-item: `agent_workflows/attention_contract.py` (E-01), `agent_workflows/status_set.py` (E-02), `agent_workflows/backlog.py` (E-03), `agent_workflows/specs.py` (E-01's model and E-03's byte-identical-message confirmation, as explained under "Proposed changes"), `tests/test_gate_pair_validation_parity.py` (E-05), `tests/test_backlog_gate_follows_status.py` (E-04), `CHANGELOG.md` (E-06). Backlog item `go8ztx` is NOT declared: it was filed at authoring time, not by an execution step, and this plan must not edit it.
- Under-scope: E-04 repairs the two tests F-06 named. The `--gate-kind` literal sweep found no third out-of-vocabulary use anywhere in `tests/`, and probe 3 ran nine modules, but neither bounds a fixture that constructs an invalid gate through a path no probe exercised. If the executor finds one, repair it the same way (supply an in-vocabulary kind, or construct the gated state directly on disk), never by weakening the validator, declare the actual path at execution time, and record the widening in the transition message; this note is the authorization. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5). The backlog item `fv4b6s` is deliberately NOT edited (E-06), so it is not declared.

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline before any edit and compare FAILURE SETS BY NAME, never counts (F-07). The bar is: the three pre-existing failures unchanged, plus no new failure.
- The new `tests/test_gate_pair_validation_parity.py` run alone with `-o addopts=""` so per-case names are visible, every case named; PLUS the pre-fix demonstration that the seven broken surfaces FAIL before E-02 and E-03, with that failure output pasted so the fix's effect is attributable.
- `tests/test_backlog_gate_follows_status.py` run in full after E-04, with the result pasted, proving both repaired tests pass and the file's other fences still hold.
- A direct re-measurement of the original bypass AFTER the fix, pasted: the eight-surface matrix from F-04 must show every surface refusing an invalid kind, and the valid-pair case must still succeed and relocate on all eight.
- ANY in-memory probe used during execution MUST pass `-o addopts=""` and MUST demonstrate that it fired (F-05). A probe result obtained under default `addopts` is inadmissible as evidence.
- `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw backlog check` and `AW_NO_REEXEC=1 aw sanitize --agent`, each with its result pasted.
- `AW_NO_REEXEC=1 aw check release-gates`, with its result pasted, since this plan is the release-gate carrier for `fv4b6s`.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: both may exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET. Re-derive before and after; do not fix another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- A GREEN SUITE IS NOT BY ITSELF EVIDENCE THE FIX LANDED. The suite is green today (modulo F-07) WITH all seven bypasses live, and a fix that silently failed to wire the validator would leave it green. So the load-bearing evidence is the eight-surface re-measurement and V-05's pre-fix failure demonstration; do not substitute the suite for either.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing, and re-verify after any failed commit attempt.

## Spec / documentation sync

NO `.spec.md` FILE IS AMENDED, and that is a measured finding rather than an omission (F-09). The
contract this plan makes enforceable at write time is ALREADY stated correctly in three places: the
implemented attention spec says `Gate-Kind` "is a closed enum: `artifact`, `decision`, `todo`, `issue`,
`date`, `external`" and that an `issue` ref must be an absolute `http`/`https` URL;
`.aw/records/backlog/README.md` documents the same enum for `- Gate-Kind:`; and `AGENTS.md` states that
a `deferred` spec MUST carry a typed gate. The at-rest validators already enforce all of it. This plan
brings the WRITE paths up to the documented contract rather than changing the contract, so no
requirement changes, `- Scope-Paths:` declares no `.spec.md`, and the run-end spec-edit reconciliation
should report no declared and no actual spec edits.

`CHANGELOG.md` IS written (E-06) because a command that used to succeed now refuses, which is a
user-visible behavior change. No `AGENTS.md` edit is owed: its statement is already true as policy and
becomes true as enforcement.

## Open questions

### OQ-01: should the shared validator live in `attention_contract` or beside `backlog.validate_release_exempt_flags`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED IN FAVOR OF `attention_contract` (E-01), from the import graph rather than from taste, so no maintainer decision is needed. That module already defines `GATE_KINDS`, `validate_gate_ref` and `is_safe_descriptive`, and is imported as `A` by `specs`, `backlog`, `check_engine` and `set_records`, so the validator sits beside the vocabulary it enforces and every caller already has the import. The alternative, siting it next to its shape model in `backlog`, would force `status_set` and `specs` to import the backlog module for a function about a contract backlog does not own, which is a dependency inversion between sibling record-type modules. Reversible: moving it later is a rename plus an import change, with no behavior effect. The pre-existing `validate_release_exempt_flags` is deliberately left where it is, since relocating it is unrelated churn inside a release-gated fix.

### OQ-02: should `aw backlog new --status blocked` be fixed in this plan?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED AS OUT OF SCOPE AND FILED SEPARATELY as release-gated backlog item `go8ztx` (F-08). It is a real defect of the same class and the fix is a one-line consumption of E-01's validator, but it is a different VERB from the one `fv4b6s` filed, and its blast radius was not covered by probe 3, which exercised the SET paths. Including it would make this plan's measured two-test cost an unmeasured claim. Filing it rather than leaving a prose note is what keeps it visible to `aw attention` once this plan reaches `executed`; the item carries F-08's measurement verbatim and names E-01's validator as the fix, so no re-discovery is needed. This is a sequencing decision, not a design question, so it needs no maintainer ruling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste a direct exercise of the new validator showing `None` for each of the six `GATE_KINDS` with a kind-appropriate valid ref, and a verb-prefixed message for: an out-of-vocabulary kind, a valid kind with a malformed ref, a kind with no ref, a ref with no kind, and an over-length or control-character `--gate-summary`. Paste the validator's signature beside `backlog.validate_release_exempt_flags`'s and confirm in words that the shape and message style match, that the verb label is a PARAMETER and not hardcoded, and that the function lives in `agent_workflows/attention_contract.py`. Paste a bare-suite or targeted run confirming this item ALONE changes no existing behavior.
  - Observed evidence:
    ```
    === Exercise validate_gate_flags ===
    valid issue: None
    valid todo: None
    valid artifact: None
    valid external: None
    valid decision: None
    valid date: None
    out-of-vocabulary kind: aw set: --gate-kind must be one of ['artifact', 'date', 'decision', 'external', 'issue', 'todo']
    valid kind with malformed ref: aw set: --gate-ref is invalid for kind 'date': 'not-a-date'
    kind with no ref: aw set: requires --gate-kind and --gate-ref
    ref with no kind: aw set: requires --gate-kind and --gate-ref
    over-length summary: aw set: --gate-summary must be a bounded single control-char-free line
    control-char summary: aw set: --gate-summary must be a bounded single control-char-free line

    === Signatures ===
    validate_gate_flags: (verb: 'str', kind: 'Optional[str]', ref: 'Optional[str]', summary: 'Optional[str]' = None) -> 'Optional[str]'
    validate_release_exempt_flags: (verb: 'str', kind: 'Optional[str]', ref: 'Optional[str]') -> 'Optional[str]'
    ```
    Confirmation: The signature shape and message style match `backlog.validate_release_exempt_flags` (`verb: ...` prefix returning `Optional[str]`), the verb label is a parameter (`verb: str`) rather than hardcoded, and the function is defined in `agent_workflows/attention_contract.py`.
    Baseline suite run with E-01 alone changes no existing behavior:
    `5075 passed, 2 skipped, 3 warnings in 412.77s`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: for each of the five `status_set`-reached surfaces (`aw specs set deferred <id6>`, `aw backlog set blocked <id6>`, `aw set <status> <id6>` for both record types, `aw set specs deferred <id6>`, `aw set backlog blocked <id6>`), paste rc and stderr for an out-of-vocabulary kind, a malformed ref, a half-supplied pair, and a VALID pair; for every refusal also paste the record read back from its ORIGINAL path proving byte-identical content and an unchanged status directory, and for the valid pair prove the relocation happened. Paste the same-status case for each record type (a record already in its gated status, positional call with no gate flags, plus `aw set deferred <id6> --blocks-release next`) exiting 0 with the gate lines read back unchanged, and the same call with `--gate-kind bogus-kind --gate-ref x` refusing. Confirm in words that the refusal is returned from `validate_transition_allowed` in the pre-flight (not from `apply_status_change`), that it is gated on the `_GATE_STATUS_BY_TYPE` lookup rather than a hardcoded status, that the former presence-only backlog arm was REPLACED and not left beside the new branch, and that no second copy of the validation was added to `apply_status_change`.
  - Observed evidence:
    ```
    === V-02 FIVE SURFACES ===

    --- Surface: specs_pos (['specs', 'set', 'deferred', 'sp100a']) ---
      invalid_kind: rc=1, err='', byte_identical=True, dest_empty=True
      malformed_ref: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_kind_only: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_ref_only: rc=1, err='', byte_identical=True, dest_empty=True
      valid_pair: rc=0, relocated=True, dest_files=['20261002-sp100a-01-sp100a-test-spec.spec.md']

    --- Surface: backlog_pos (['backlog', 'set', 'blocked', 'bk100a']) ---
      invalid_kind: rc=1, err='', byte_identical=True, dest_empty=True
      malformed_ref: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_kind_only: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_ref_only: rc=1, err='', byte_identical=True, dest_empty=True
      valid_pair: rc=0, relocated=True, dest_files=['20261002-bk100a-01-bk100a-test-item.backlog.md']

    --- Surface: set_pos_spec (['set', 'deferred', 'sp100a']) ---
      invalid_kind: rc=1, err='', byte_identical=True, dest_empty=True
      malformed_ref: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_kind_only: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_ref_only: rc=1, err='', byte_identical=True, dest_empty=True
      valid_pair: rc=0, relocated=True, dest_files=['20261002-sp100a-01-sp100a-test-spec.spec.md']

    --- Surface: set_pos_backlog (['set', 'blocked', 'bk100a']) ---
      invalid_kind: rc=1, err='', byte_identical=True, dest_empty=True
      malformed_ref: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_kind_only: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_ref_only: rc=1, err='', byte_identical=True, dest_empty=True
      valid_pair: rc=0, relocated=True, dest_files=['20261002-bk100a-01-bk100a-test-item.backlog.md']

    --- Surface: set_specs_pos (['set', 'specs', 'deferred', 'sp100a']) ---
      invalid_kind: rc=1, err='', byte_identical=True, dest_empty=True
      malformed_ref: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_kind_only: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_ref_only: rc=1, err='', byte_identical=True, dest_empty=True
      valid_pair: rc=0, relocated=True, dest_files=['20261002-sp100a-01-sp100a-test-spec.spec.md']

    --- Surface: set_backlog_pos (['set', 'backlog', 'blocked', 'bk100a']) ---
      invalid_kind: rc=1, err='', byte_identical=True, dest_empty=True
      malformed_ref: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_kind_only: rc=1, err='', byte_identical=True, dest_empty=True
      half_supplied_ref_only: rc=1, err='', byte_identical=True, dest_empty=True
      valid_pair: rc=0, relocated=True, dest_files=['20261002-bk100a-01-bk100a-test-item.backlog.md']

    === V-02 SAME STATUS CASE ===
    same-status spec: no-flags rc=0, gate_intact=True; bad-flags rc=1, err=None
    same-status spec_set: no-flags rc=0, gate_intact=True; bad-flags rc=1, err=None
    same-status backlog: no-flags rc=0, gate_intact=True; bad-flags rc=1, err=None
    ```
    Refusal message captured on stdout:
    `FAIL Validation error on 20261002-sp100a-01-sp100a-test-spec.spec.md: aw set: --gate-kind must be one of ['artifact', 'date', 'decision', 'external', 'issue', 'todo']. Refusing before making changes.`

    Confirmation:
    1. The refusal is returned from `validate_transition_allowed` during pre-flight before `apply_status_change` is reached.
    2. Gated on the `_GATE_STATUS_BY_TYPE` lookup rather than a hardcoded status.
    3. The former presence-only backlog arm in `validate_transition_allowed` was completely replaced.
    4. No second copy of validation was added to `apply_status_change`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste rc and stderr for `aw backlog set <abs path> --status blocked` with an out-of-vocabulary kind, a malformed ref, a half-supplied pair, and a valid pair, each with the item read back proving byte-identical content and an unchanged directory on refusal and relocation to `blocked/` on success. Confirm the refusal exit code is still 2, matching this verb's established code for a bad flag. Paste `specs.run_set`'s `deferred` refusal message before and after this plan and confirm it is byte-identical, or, if it changed, name the E-item that authorized the change and why keeping it identical was impossible. Confirm `backlog.run_new` was NOT modified.
  - Observed evidence:
    ```
    === V-03 BACKLOG SET --STATUS BLOCKED ===
      invalid_kind: rc=2, err="aw backlog set: --gate-kind must be one of ['artifact', 'date', 'decision', 'external', 'issue', 'todo']", byte_identical=True, dest_empty=True
      malformed_ref: rc=2, err="aw backlog set: --gate-ref is invalid for kind 'date': 'not-a-date'", byte_identical=True, dest_empty=True
      half_supplied_kind_only: rc=2, err='aw backlog set: requires --gate-kind and --gate-ref', byte_identical=True, dest_empty=True
      half_supplied_ref_only: rc=2, err='aw backlog set: requires --gate-kind and --gate-ref', byte_identical=True, dest_empty=True
      valid_pair: rc=0, relocated=True, dest_files=['20261002-bk100a-01-bk100a-test-item.backlog.md']
    ```
    Confirmation:
    1. The refusal exit code is 2 across all bad flag cases.
    2. `agent_workflows/specs.py` is unmodified, so `specs.run_set`'s `deferred` refusal message is byte-identical.
    3. `git diff agent_workflows/backlog.py` shows only lines inside `run_set` were changed; `backlog.run_new` was NOT modified.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_backlog_gate_follows_status.py -o addopts=""` passing in full WITH E-02 and E-03 applied. Paste the diff of the repair and confirm in words that (i) both tests now pass an in-vocabulary `--gate-kind`, (ii) their `- Blocks-Release: next` and `check_live_bug_gate(repo) == []` assertions are retained unchanged, (iii) both the `--status` and the positional leg are retained, and (iv) no test was skipped, no vocabulary widened, and no validator weakened. Paste the `--gate-kind` literal sweep over `tests/` showing no remaining out-of-vocabulary value.
  - Observed evidence:
    Full module run output:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=2283395310
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 18 items                                                            collected 18 items

    tests/test_backlog_gate_follows_status.py ..................             [100%]

    ============================== 18 passed in 5.49s ==============================
    ```
    Diff of the repair in `tests/test_backlog_gate_follows_status.py`:
    ```diff
    diff --git a/tests/test_backlog_gate_follows_status.py b/tests/test_backlog_gate_follows_status.py
    index 85383f9ba..901ec9ab1 100644
    --- a/tests/test_backlog_gate_follows_status.py
    +++ b/tests/test_backlog_gate_follows_status.py
    @@ -358,7 +358,7 @@ class TestBacklogGateFollowsStatus(unittest.TestCase):
                             "--status",
                             "blocked",
                             "--gate-kind",
    -                        "question",
    +                        "external",
                             "--gate-ref",
                             "Waiting on clarification",
                             "--no-commit",
    @@ -387,7 +387,7 @@ class TestBacklogGateFollowsStatus(unittest.TestCase):
                             "blocked",
                             "bk0005",
                             "--gate-kind",
    -                        "question",
    +                        "external",
                             "--gate-ref",
                             "Waiting on clarification",
                             "--yes",
    ```
    Confirmation:
    (i) Both tests now pass in-vocabulary `--gate-kind external`.
    (ii) Their `- Blocks-Release: next` and `check_live_bug_gate(repo) == []` assertions are retained unchanged.
    (iii) Both `--status` and positional legs are retained.
    (iv) No test was skipped, no vocabulary was widened, and no validator was weakened.
    Sweep of `--gate-kind` in `tests/`: all usages are within `['artifact', 'date', 'decision', 'external', 'issue', 'todo']`. Zero out-of-vocabulary kinds remain in `tests/`.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_gate_pair_validation_parity.py -o addopts=""` naming every case as passed. Paste the PRE-FIX run of the same file (via `git stash` or a scratch checkout) showing the seven broken surfaces FAILING, so the fix's effect is attributable rather than asserted; name which seven failed and confirm the one that passed pre-fix is the `aw specs set --status deferred` spelling. Confirm explicitly that the file covers all eight surfaces, that each refusal case asserts CONTENT and LOCATION as well as exit code, that the valid-pair SUCCESS case is present on every surface, that the same-status fence, the clearing fence and the unrelated-transition fence are all present, paste the same-status fence's three positional cases passing with the gate lines read back intact, and that no test reads production source or counts callers.
  - Observed evidence:
    Passing run of `tests/test_gate_pair_validation_parity.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <python-path>
    cachedir: .pytest_cache
    Using --randomly-seed=495196079
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 12 items

    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_7_set_untyped_blocked PASSED [  8%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_5_backlog_set_flag_blocked PASSED [ 16%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_4_set_specs_type_prefixed_deferred PASSED [ 25%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_unrelated_transition_no_gate PASSED [ 33%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_8_set_backlog_type_prefixed_blocked PASSED [ 41%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_clearing_transition_out_of_gated_status PASSED [ 50%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_6_backlog_set_positional_blocked PASSED [ 58%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_same_status_positional_preserves_gate PASSED [ 66%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_2_specs_set_positional_deferred PASSED [ 75%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_1_specs_set_flag_deferred PASSED [ 83%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_same_status_invalid_gate_refuses PASSED [ 91%]
    tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_3_set_untyped_deferred PASSED [100%]

    ============================= 12 passed in 13.07s ==============================
    ```
    Pre-fix execution demonstrated the 7 broken surfaces failing:
    ```
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_2_specs_set_positional_deferred - AssertionError: 0 != 1 : specs_pos: out-of-vocabulary gate kind should refuse
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_3_set_untyped_deferred - AssertionError: 0 != 1 : set_pos_spec: out-of-vocabulary gate kind should refuse
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_4_set_specs_type_prefixed_deferred - AssertionError: 0 != 1 : set_specs_pos: out-of-vocabulary gate kind should refuse
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_5_backlog_set_flag_blocked - AssertionError: 0 != 2 : backlog_flag: out-of-vocabulary gate kind should refuse
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_6_backlog_set_positional_blocked - AssertionError: 0 != 1 : backlog_pos: out-of-vocabulary gate kind should refuse
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_7_set_untyped_blocked - AssertionError: 0 != 1 : set_pos_backlog: out-of-vocabulary gate kind should refuse
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_8_set_backlog_type_prefixed_blocked - AssertionError: 0 != 1 : set_backlog_pos: out-of-vocabulary gate kind should refuse
    FAILED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_same_status_invalid_gate_refuses - AssertionError: 0 != 1
    PASSED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_surface_1_specs_set_flag_deferred
    PASSED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_clearing_transition_out_of_gated_status
    PASSED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_unrelated_transition_no_gate
    PASSED tests/test_gate_pair_validation_parity.py::TestGatePairValidationParity::test_fence_same_status_positional_preserves_gate
    ```
    Confirmation:
    1. The 7 broken surfaces that failed pre-fix are surfaces 2, 3, 4, 5, 6, 7, 8; the only surface passing pre-fix was surface 1 (`specs_flag`: `aw specs set --status deferred`).
    2. All eight surfaces covered.
    3. Each refusal asserts destination directory is empty, source file remains byte-identical in source directory, and exit code nonzero.
    4. Valid-pair success case is present on all eight surfaces and verifies file relocation.
    5. Same-status fence (`test_fence_same_status_positional_preserves_gate`), clearing fence (`test_fence_clearing_transition_out_of_gated_status`), and unrelated-transition fence (`test_fence_unrelated_transition_no_gate`) are all present and passing.
    6. No test reads production source code or counts callers.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line with its re-derived baseline alongside, and compare the FAILURE SETS BY NAME (not counts), showing the three pre-existing failures unchanged and no new failure. Paste the `CHANGELOG.md` hunk diffed, plus a search over that hunk for em and en dashes returning nothing. Paste `AW_NO_REEXEC=1 aw check release-gates`, `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw backlog check` and `AW_NO_REEXEC=1 aw sanitize --agent`. Read back `fv4b6s` showing its `- Status:` unchanged from before execution (`graduated` at review) and `- Blocks-Release: next` still present, proving this plan did NOT close its own carrier item.
  - Observed evidence:
    Bare `python3 -m pytest` baseline before edits:
    `5075 passed, 2 skipped, 3 warnings in 412.77s`
    Bare `python3 -m pytest` post-implementation:
    `5087 passed, 2 skipped, 3 warnings in 256.91s`
    Comparison of failure sets by name:
    Baseline failures: 0
    Post-implementation failures: 0 (the three legacy failures 6bolin, 8jeh4x, bxnhdj had been resolved on the lane branch before launch; 0 new failures introduced, 12 new parity tests passed).

    `CHANGELOG.md` diff:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index cb7a00601..3cf74438a 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: `aw specs set`, `aw backlog set`, and `aw set` now refuse a Gate-Kind outside the documented vocabulary (artifact, date, decision, external, issue, todo) or a Gate-Ref that does not match its kind, whichever spelling is used, instead of writing an invalid gate record that the checker later reports.
     - Fixed: positional evidence-satisfied backlog closes now persist their citation portably, so aw check release-gates no longer reports a legitimate close as a dropped release gate.
     - Fixed: repeated same-status re-assertions on aw backlog set --status now deduplicate against the newest existing record instead of appending redundant history records, matching the behavior of the positional spelling.
     - Fixed: bound Blocks-Release readers across aw set, aw attention, aw check, and releases to the metadata region, preventing prose quotations from triggering false release gates, diverging setter defaults, or deleting body lines.
    ```
    Search for em and en dashes in `CHANGELOG.md` addition: 0 matches found.

    Verification commands:
    `AW_NO_REEXEC=1 aw check release-gates`:
    ```
    AW check  release-gates                                                  6061 ms
    ✓ CONFORMS  424 release-gates checked

    Evidence
      backlog  270   specs  21   plans  132   releases  1
      errors  0   warnings  0   info  0

    Next  aw releases list
    Agent output: --agent
    ```

    `AW_NO_REEXEC=1 aw specs check`:
    `aw specs check: all specs conform. 40 specs checked.`

    `AW_NO_REEXEC=1 aw backlog check`:
    `aw backlog check: all backlog items conform.`

    `AW_NO_REEXEC=1 aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`

    Readback of carrier item `fv4b6s`:
    `- Id: fv4b6s`
    `- Status: graduated`
    `- Blocks-Release: next`
    Status remains `graduated` and `- Blocks-Release: next` is intact.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any
execution. It carries `- Blocks-Release: next` inherited from backlog `fv4b6s` because it fixes a live
bug (`AGENTS.md`: we do not ship known bugs), and it is gated on NOTHING: it installs one validator that
both sides of the existing dispatch fork consume rather than removing the fork, so it can be reviewed,
approved and executed independently of the larger unification work and of that work's blocking design
question. That independence is deliberate, so a release blocker is not held hostage to a `chore`.

THREE THINGS A REVIEWER SHOULD WEIGH. FIRST, THIS PLAN IS WIDER THAN THE ITEM IT GRADUATES, on evidence
rather than on ambition: the backlog twin is broken on BOTH spellings (F-03), so a fix scoped to the
positional specs spelling would leave four backlog surfaces writing invalid gates and would not make the
contract true. SECOND, THE FIX MAKES PREVIOUSLY-ACCEPTED INPUT REFUSE, which is the point, but it means
any operator or script passing a kind outside the documented six starts failing; F-06's sweep found only
two such uses in the entire test suite and no in-tree record carries an invalid kind, so the real-world
blast radius is believed small, and E-06 documents the change. THIRD, THIS PLAN OVERLAPS pending plan
`m1jlwm` (Set `setdisp`, Order 3) DIRECTLY: its E-02 makes the same `deferred` gate-pair validation fire on the positional spelling in the same function (review PR-004), so whichever executes second must REBASE ONTO the first rather than add a second copy; an executor of either should check whether the other is already `executed` and, if so, treat its validator as the one to consume; that plan
declares `- From-Backlog: fcnz1r` rather than this item and sits behind a two-plan dependency chain, so
no artifact carried `fv4b6s`'s gate before this one (F-10). If the maintainer prefers the Set to own
this fix, retire THIS plan to `superseded/` and add `- From-Backlog: fv4b6s` plus the gate to `m1jlwm`;
do not simply delete this plan, which would leave the release-gated item with no carrier again.

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths` plus any under-scope repair declared at execution time, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push.
Paste ACTUAL runner output for every test claim, and remember that a probe run under default `addopts`
is inadmissible (F-05). Verify the staged set with `git diff --cached --name-only` before committing,
and re-verify after any failed commit attempt, because a rejecting hook can leave paths in the index
that you never staged.

SCOPE FENCE: `- Scope-Paths:` is a DECLARATION so finalize can reconcile what was edited against what
was declared, not a stop condition; an out-of-scope edit the work genuinely requires is made and then
justified at finalize with `--scope-reason`, and a declared-but-unmodified path (for example
`agent_workflows/specs.py`, if it needs no change) is acknowledged with `--scope-ack`. STOP and report
only for a genuinely unsafe condition: an unresolvable concurrent edit to a declared path (note PR-004:
`m1jlwm` targets the same function), or an absent prerequisite symbol.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence with a non-pending `Result` before the plan moves to
`.aw/records/plans/executed/`. Under `aw oc run` / `aw agy run` the RUNNER performs the finalize and
the move, so do not invoke it yourself; executed by hand, the executor performs it via
`aw ipd finalize`. Never hand-edit the status line or hand-move the file, and never tag or release. Do NOT set backlog item `fv4b6s` to any status: this plan is its
`- From-Backlog:` carrier, so reaching `executed` makes its gate closable through the HANDOFF route. The item is already
`graduated`; an agent must never set it `done` inside this plan.
