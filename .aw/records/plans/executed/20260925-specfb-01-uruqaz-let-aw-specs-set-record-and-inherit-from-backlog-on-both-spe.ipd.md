# IPD: Let aw specs set record and inherit From-Backlog on both spellings

- Date: 2026-09-25
- Kind: child
- Concern: `aw specs set` has no `--from-backlog` flag, so a spec that graduates from a backlog item cannot record the link through a setter or inherit the item's release gate. The bare `aw specs set <status> <sel>` spelling routes through `status_set` (which already writes the field when told to), but the `--status` spelling routes through `specs.run_set`, which has no writer for it.
- Scope: IN: register `--from-backlog` on `specs set`; write it and inherit `Blocks-Release` the way `aw ipd set --from-backlog` does on the `--status` spelling (the bare spelling already does both, proven at review); tests for both spellings including the three precedence rules; correct the one AGENTS.md sentence that names only a plan route. OUT: `aw specs new`; `command_surface.py` (review measured the declaration is leaf-scoped, not flag-scoped, so nothing is owed there); any id6-validation refusal (shipped policy is write-never-refuse).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/specs.py, tests/test_specs_from_backlog.py, AGENTS.md, .aw/records/specs/README.md, .aw/records/backlog/README.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- Set: specfb
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: uruqaz
- From-Backlog: mod4ml

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: uruqaz verified (set specfb, attempt 1). [Scope reconciliation - in-scope-unmodified .aw/records/backlog/README.md: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified .aw/records/specs/README.md: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 8 findings PR-501..PR-508 all FIXED, 5 decisions D-1..D-5 recorded; review record written; aw ipd lint --phase review-finalize conforming
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog mod4ml. Verified at HEAD: `specs set --help` has no `--from-backlog`; the `--status` path in `specs.run_set` writes Priority, Work-Kind and Graduated-To but not From-Backlog.

## Goal

A spec-first graduation records its backlog source and carries the item's release gate through the same setter a plan uses.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: flag and writers

- [x] E-01 Register `--from-backlog` on the `specs set` parser (`cli.py`'s `p_specs_set`, beside the `--graduated-to` registration whose comment already states the both-spellings obligation this plan discharges), with `dest="from_backlog"`, `default=None`, and help text matching `p_ipd_set`'s (`"Link this spec to the backlog item it graduated from (a backlog id6); '-' clears it."`, substituting spec for plan).
  - Depends on: none
  - Expected outcome: `python3 -m agent_workflows specs set --help` lists `--from-backlog`. That ALONE makes the BARE spelling fully work, proven at review by driving `status_set.run_set_command` directly with `from_backlog="bbb111"` on a scratch repo: it wrote `- From-Backlog: bbb111`, inherited `- Blocks-Release: relaaa`, printed the inheritance line, and relocated the spec. So no writer work is owed on that path, exactly as the source item `mod4ml` predicted for it.
  - Do NOT touch `command_surface.py`, and do NOT add it to `Scope-Paths`. The original wording called for adding the flag to the `specs set` `legacy_flags`, and review measured that this is neither required nor correct: `COMMAND_INVENTORY` declares parser LEAVES, not flags (`command_surface.discover_parser_leaves`), the conformance matrix's hard failure is an undeclared LEAF, and the single shared `command="set"` declaration lists neither `--from-backlog` nor `--graduated-to` nor `--priority` nor `--work-kind` today. Adding one flag to that list would make the field look enumerated while four siblings are absent, which is worse than the current consistent silence.
  - Execution state: performed

- [x] E-02 In `specs.run_set` (the `--status` spelling), write the field through `releases.set_from_backlog_line`, placed beside the existing `--graduated-to` writer whose comment states the reason this call has to exist at all. Measured at review by driving `specs.run_set` with `from_backlog="bbb111"` on the same scratch repo: rc 0, the spec relocated, and BOTH `- From-Backlog:` and `- Blocks-Release:` ABSENT from the result, so the flag is silently dropped on this path.
  - Depends on: E-01
  - Expected outcome: both spellings write the field identically.
  - Read the value with `getattr(args, "from_backlog", None)`, matching the four writers above it. This is not style: `specs.run_set` is called throughout the suite with a hand-built `argparse.Namespace` that sets only the attributes a given test needs (`tests/test_specs_verbs.py`'s `_args`, `tests/test_specs_status_dirs.py`), so a direct `args.from_backlog` raises `AttributeError` across existing tests that this plan must not break.
  - Execution state: performed

- [x] E-03 Port the gate inheritance to the `--status` path, in the SAME shape `status_set` uses, so the two spellings cannot disagree about a release gate: when `from_backlog` is neither `None` nor `-`, no explicit `--blocks-release` was passed, and the spec carries no `- Blocks-Release:` bullet already, read the item's gate with `backlog.blocks_release_of_item` and write it with `releases.set_blocks_release_line`, printing the same inheritance line (`aw set: inherited - Blocks-Release: <r> from backlog item <id6> (graduation handoff: the gate travels with the work)`).
  - Depends on: E-02
  - Expected outcome: a gated item's gate reaches the spec on BOTH spellings, and an existing gate on the spec is never overwritten.
  - PRESERVE THE THREE PRECEDENCE RULES the shipped implementation states at `status_set.py` (`IT IS A WRITE, NEVER A REFUSAL`): an explicit `--blocks-release` in the same call WINS, an existing gate on the artifact is NEVER overwritten (it may encode a decision the spec made for its own reasons), and a missing or unresolvable item is NOT a refusal. Re-read that comment before writing this item; a divergent precedence order here would be a silent cross-spelling inconsistency of exactly the kind this plan exists to remove.
  - This is split from E-02 deliberately: the field write is a one-line call with no policy, and the gate inheritance carries three precedence rules and a second artifact read. They fail differently and need different evidence.
  - Execution state: performed

### Task group 2: tests and docs

- [x] E-04 Add `tests/test_specs_from_backlog.py`: for EACH spelling (`status_set.run_set_command` with `status=None`, and `specs.run_set` with an explicit `status`), a scratch repo holding a draft spec, a release record, and an `open` backlog item carrying `- Blocks-Release:`; assert `--from-backlog <id6>` writes `- From-Backlog: <id6>` and inherits `- Blocks-Release:`. Add the three precedence cases E-03 must preserve, asserted on BOTH spellings: an explicit `--blocks-release` wins; an existing gate on the spec is NOT overwritten; and `-` clears the field without inheriting anything.
  - Depends on: E-03
  - Expected outcome: all pass; the `--status` cases fail before E-02/E-03.
  - Follow the scratch-repo shape `tests/test_specs_status_dirs.py` already uses for both spellings (a real `git init` repo under a temp dir, records written under `.aw/records/...`, `no_commit=True`), and build the Namespace explicitly as that file does.
  - Do NOT assert a refusal for an unknown id6. The original E-03 required one, and review measured that it would contradict shipped policy: `status_set`'s own comment rules the write is NEVER a refusal because refusing would break a link the author is legitimately recording, and `check.from-backlog-dangling` already ships at ERROR to catch it afterwards. Asserting a refusal would also make the two spellings disagree, which is the defect this plan removes. See OQ-02.
  - Execution state: performed

- [x] E-05 Correct `AGENTS.md`'s Release gates section, which names `aw ipd set <status> <plan> --from-backlog <id6>` as THE way to set the field and then says a spec is an equally valid gate carrier without giving a spec route (the exact asymmetry `mod4ml` describes). State that `aw specs set` carries the same flag on both spellings. The section sits BELOW the `<!-- /aw:block -->` marker, so it is repo-local prose and not installer-managed; verify that before editing.
  - Depends on: E-04
  - Expected outcome: the doc names a spec route that now exists.
  - Also grep `.aw/records/specs/README.md` and `.aw/records/backlog/README.md` for a claim that a spec cannot record the field through a setter and correct any hit. Measured at review: neither file mentions `from-backlog` at all, so this half is expected to be a no-op and must be REPORTED as such rather than reported as a fix. Leave AGENTS.md's adjacent `there is no --from-spec setter yet` sentence ALONE: it is about a different field and is still true.
  - Execution state: performed

- [x] E-06 Run the bare suite (`python3 -m pytest`, no added flags) and paste the actual summary line.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: 0 failed, and any failure named as pre-existing with evidence from the base commit or as new.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The two `aw specs set` spellings route to different handlers, dispatched on whether `--status` is present (`cli.py`'s `specs_cmd == "set"` branch: `status is None` -> `status_set.run_set_command`, else `specs.run_set`), and every field writer must exist on both, as the existing `Graduated-To` comment in `specs.run_set` explains.
- `specs.run_set` reads every optional field with `getattr(args, <name>, None)`, because the suite calls it with hand-built Namespaces carrying only the attributes a test needs. A new field must follow that, or existing tests raise `AttributeError`.
- The gate-inheritance policy is WRITE, NEVER REFUSE (`status_set.py`, `IT IS A WRITE, NEVER A REFUSAL`), with an explicit `--blocks-release` winning and an existing gate never overwritten. A new surface inherits that policy rather than inventing one.
- `command_surface.COMMAND_INVENTORY` declares parser LEAVES, not flags. The conformance matrix hard-fails on an undeclared leaf; `legacy_flags` is an incomplete convenience list (the shared `set` declaration names none of `--priority`, `--work-kind`, `--graduated-to`, `--from-backlog`).
- AGENTS.md's Release gates section is BELOW `<!-- /aw:block -->`, so it is repo-local prose that a plan may edit; the managed block ends at the marker.

## Findings

F-1 and F-2 were measured by the author at HEAD `0c2e7970` and both reproduce at review HEAD `bd2aae40`. F-3 through F-7 were measured at `/plan-review` (2026-09-25), several by EXECUTING the two handlers against a scratch repo rather than by reading them.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `cli` `specs set` | No `--from-backlog` flag. | `specs set --help` lists no such flag; `specs set draft zzzz99 --from-backlog mod4ml` -> `error: unrecognized arguments` |
| F-2 | LOW | `specs.run_set` | No From-Backlog writer on the `--status` path. | read `specs.run_set`; PROVEN by execution at review (below) |
| F-3 | LOW | both handlers | THE TWO PATHS ARE ASYMMETRIC IN THE OPPOSITE DIRECTIONS THE PLAN ASSUMED, and measuring it re-sized two items. The BARE spelling is already COMPLETE: driving `status_set.run_set_command` with `from_backlog="bbb111"` on a scratch repo wrote `- From-Backlog: bbb111`, inherited `- Blocks-Release: relaaa`, printed the inheritance line and relocated the spec, so E-01's flag registration alone finishes that path. The `--status` spelling drops BOTH silently: the same call through `specs.run_set` returned rc 0, relocated the spec, and produced neither bullet. | Two scripted runs at review against a scratch git repo holding a draft spec, a `planned` release record, and an `open` item carrying `- Blocks-Release: relaaa` |
| F-4 | MEDIUM | original E-02's id6 validation | THE PROPOSED VALIDATION CONTRADICTS SHIPPED POLICY AND WOULD RE-CREATE THE ASYMMETRY THIS PLAN REMOVES. E-02 required validating the id6 against `backlog.existing_backlog_ids` and (per E-03) refusing an unknown one. The shipped write states the opposite as a deliberate ruling: refusing would break a link the author is legitimately recording, and `check.from-backlog-dangling` already ships at ERROR to catch it. `status_set` performs NO validation, so adding it on one spelling only would leave the two disagreeing about the same flag. | `status_set.py` `IT IS A WRITE, NEVER A REFUSAL` comment and its gate-inheritance body, which calls `blocks_release_of_item` and never `existing_backlog_ids`; `releases.check_from_backlog` ships the ERROR-severity rule |
| F-5 | LOW | original E-01's `command_surface` step | NOTHING IS OWED IN `command_surface.py`, and adding the flag there would make the surface LESS honest. `COMMAND_INVENTORY` declares parser LEAVES; the matrix's hard failure is an undeclared LEAF, not an undeclared flag. The single shared `command="set"` declaration lists none of `--priority`, `--work-kind`, `--graduated-to`, so adding `--from-backlog` alone would imply an enumeration that does not exist. | `command_surface.discover_parser_leaves` docstring and `build_matrix`'s `report.undeclared = sorted(parser_leaves - declared)`; the `command="set"` declaration's `legacy_flags` tuple; `tests/test_json_and_exitcodes.py` passes untouched |
| F-6 | LOW | original E-04's doc grep | THE GREP TARGET IS THE WRONG SHAPE, so the item would have reported a clean no-op over a real doc defect. No file says "a spec cannot record the field"; what AGENTS.md actually does is name `aw ipd set <status> <plan> --from-backlog <id6>` as THE setter and then say a spec is an equally valid carrier, giving no spec route. That IS the asymmetry `mod4ml` describes, stated positively rather than as a denial. Neither records README mentions `from-backlog` at all. | `grep -n "from-backlog" AGENTS.md .aw/records/specs/README.md .aw/records/backlog/README.md` -> 4 hits, all in AGENTS.md, none in either README |
| F-7 | LOW | `specs.run_set` call convention | A DIRECT `args.from_backlog` WOULD BREAK EXISTING TESTS. The suite builds Namespaces holding only the attributes each test needs (`tests/test_specs_verbs.py`'s `_args` sets five or six; `tests/test_specs_status_dirs.py` sets a fixed list), which is why every optional field in `specs.run_set` is read with `getattr(..., None)`. | read `specs.run_set`'s four existing field reads and both test files' Namespace construction |

## Proposed changes (ordered, validatable)

1. E-01: register the flag, which alone completes the bare spelling (F-3).
2. E-02: the field write on the `--status` path.
3. E-03: the gate inheritance on the `--status` path, preserving the three shipped precedence rules.
4. E-04: tests for both spellings, including the three precedence cases, and no refusal assertion (F-4).
5. E-05: correct the one AGENTS.md sentence that names only a plan route (F-6).
6. E-06: bare suite.

## Deferred / out of scope (with reason)

- `aw specs new --from-backlog`.
  - Carrier-Declined: a spec created from an item can set the field with the setter immediately after; one route is enough to close the gap mod4ml names.
- VALIDATING the id6 (or refusing an unknown one) on either spelling.
  - Carrier-Declined: this is a DECLINE, not a deferral. Shipped policy rules the write is never a refusal, and `check.from-backlog-dangling` already catches a dangling link at ERROR severity, so there is no uncovered gap to carry. Filing an item would record an intent the repository has explicitly decided against.
- DECLARING `--from-backlog` in `command_surface.py`'s `legacy_flags`.
  - Carrier-Declined: nothing is outstanding. The declaration is leaf-scoped (F-5) and four sibling flags are equally absent, so the current state is consistent rather than incomplete. If the repository ever decides `legacy_flags` should enumerate every flag, that is a surface-wide decision about 132 declarations and not a residue of this plan.

## Scope check

- Over-scope: two items were REMOVED as over-scope, each traceable to no requirement: the `command_surface.py` declaration (F-5) and the id6-validation refusal (F-4), which was additionally traceable AGAINST a shipped ruling. `command_surface.py` was dropped from `Scope-Paths` accordingly.
- Under-scope: two gaps closed. The gate inheritance on the `--status` path was bundled into E-02's prose but had no item of its own and no precedence rules; it is now E-03 with the three rules named. And the doc correction was keyed on a sentence that does not exist while the real defect (AGENTS.md naming only a plan route) went unnamed; E-05 now names it.

## Required tests / validation

- `python3 -m pytest tests/test_specs_from_backlog.py -o addopts="" -q` plus the V-04 revert.
- `python3 -m pytest tests/test_specs_verbs.py tests/test_specs_status_dirs.py tests/test_spec_review_attestation.py -o addopts="" -q`. REQUIRED, not optional: these three build `specs.run_set` Namespaces by hand (F-7), so they are what a direct attribute read would break, and a run scoped to the new file alone would not exercise them.
- Bare `python3 -m pytest`.

## Spec / documentation sync

No spec record is amended, so this plan declares no spec edit and the runners' spec-edit announcement should report none. The only prose change is E-05's correction to `AGENTS.md`'s Release gates section, which names `aw ipd set ... --from-backlog` as the setter and asserts a spec is an equally valid gate carrier while giving no spec route (F-6). That section is BELOW `<!-- /aw:block -->`, so it is repo-local and not installer-managed; the executor must confirm that before editing, because a managed-block edit would be overwritten by the next install. The two records READMEs mention `from-backlog` nowhere, so that half of the grep is expected to be a no-op and must be reported as one.

## Open questions

### OQ-01: Should the flag accept `-` to clear?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, resolved from the sibling: `aw ipd set --from-backlog -` clears, and a spec's From-Backlog is optional, so the two setters stay symmetric. CONFIRMED at review that `-` is load-bearing beyond symmetry: `status_set` guards the gate inheritance with `if fb != "-"`, so `-` must reach the writer as a literal rather than being normalized away, and E-03 must carry the same guard.

### OQ-02: Should either spelling validate the `--from-backlog` id6 and refuse an unknown one?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The plan as authored required it (E-02 "validate the id6 against `backlog.existing_backlog_ids`", E-03 "an unknown id6 is refused"), and review resolved it AGAINST that from the shipped implementation, which states the ruling explicitly at `status_set.py`: `IT IS A WRITE, NEVER A REFUSAL. Refusing --from-backlog when the gate cannot be applied would break a link the author is legitimately recording, and check.from-backlog-gate-mismatch already ships at ERROR to catch a mismatch afterwards.` Two independent reasons follow. FIRST, `check.from-backlog-dangling` already ships at ERROR severity and scans specs as well as plans, so an unknown id6 is caught by the portable authority rather than being silently accepted. SECOND, and decisively for THIS plan: `status_set` performs no validation, so validating on the `--status` spelling alone would leave the two spellings disagreeing about the same flag, which is the exact defect the plan exists to remove. Resolved from repository evidence rather than asked because the repository states the ruling and the reason in a comment beside the code being extended. This is REVERSIBLE: if validation is ever wanted it belongs on both spellings at once, as its own change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `python3 -m agent_workflows specs set --help` excerpt showing `--from-backlog`; AND paste a driven BARE-spelling run on a scratch repo (a draft spec, a `planned` release record, an `open` item carrying `- Blocks-Release:`) showing the resulting spec carries `- From-Backlog:` and the inherited `- Blocks-Release:`, plus the inheritance line on stdout. The second half is required because F-3 measured that the flag registration alone completes this path, and a `--help` line proves only that the flag parses.
  - Observed evidence: Verified `--help` lists `--from-backlog`, and bare spelling driven on a scratch repo successfully inherited gate and recorded link:
    ```text
    $ python3 -m agent_workflows specs set --help
      --from-backlog FROM_BACKLOG
                            Link this spec to the backlog item it graduated from
                            (a backlog id6); '-' clears it.
    ```
    Driven bare spelling run on scratch repo:
    ```text
    aw set: inherited - Blocks-Release: relaaa from backlog item bkl001 (graduation handoff: the gate travels with the work)
    -    spec        20260925-sp0001-01-sp0001  draft → ◔  to-review
    RC: 0
    Dest exists: True
    Dest content:
    # Spec: My Spec

    - Date: 2026-09-25
    - Status: to-review
    - Blocks-Release: relaaa
    - From-Backlog: bkl001
    - Id: sp0001
    - Author: tester

    ## Workflow history
    - 2026-09-26 to-review (tester): moving to review

    - 2026-09-25 draft (tester): created
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff; AND paste a driven `--status`-spelling run showing `- From-Backlog:` now present in the written file. A diff alone does not distinguish a writer that runs from one placed after an early return, which is the failure this path already exhibits.
  - Observed evidence: Verified diff and driven run writing `- From-Backlog:` on the `--status` path:
    Diff:
    ```diff
    --- a/agent_workflows/specs.py
    +++ b/agent_workflows/specs.py
    @@ -802,6 +802,31 @@ def run_set(args) -> int:
             new_text = _releases.set_graduated_to_line(new_text, _gt_canonical)
    +    # uruqaz E-02/E-03: write From-Backlog and inherit the item's release gate on the `--status` path,
    +    # matching the bare spelling handled by `status_set.py`.
    +    from_backlog_arg = getattr(args, "from_backlog", None)
    +    if from_backlog_arg is not None:
    +        from agent_workflows import releases as _releases
    +
    +        new_text = _releases.set_from_backlog_line(new_text, from_backlog_arg)
    +        if from_backlog_arg != "-" and getattr(args, "blocks_release", None) is None:
    +            from agent_workflows import backlog as _backlog
    +
    +            _carrier_m = re.search(
    +                r"(?m)^- Blocks-Release:[ \t]*(\S+)[ \t]*$", new_text
    +            )
    +            if _carrier_m is None:
    +                _item_gate = _backlog.blocks_release_of_item(
    +                    _repo_root_of(path), from_backlog_arg
    +                )
    +                if _item_gate:
    +                    new_text = _releases.set_blocks_release_line(
                        new_text, _item_gate
                    )
                    sys.stdout.write(
                        f"aw set: inherited - Blocks-Release: {_item_gate} from backlog item "
                        f"{from_backlog_arg} (graduation handoff: the gate travels with the work)\n"
                    )
    ```
    Driven `--status`-spelling run:
    ```text
    aw set: inherited - Blocks-Release: relaaa from backlog item bkl001 (graduation handoff: the gate travels with the work)
    aw specs set: <scratch>/.aw/records/specs/to-review/20260925-sp0001-01-sp0001-spec-a.spec.md -> to-review
    Written spec metadata bullets:
      - Status: to-review
      - Blocks-Release: relaaa
      - From-Backlog: bkl001
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff and FOUR driven `--status`-spelling outcomes, since the precedence rules are the substance of this item: (a) a gated item's gate is inherited and the inheritance line printed; (b) an explicit `--blocks-release` in the same call WINS over the item's gate; (c) a spec that already carries `- Blocks-Release:` is NOT overwritten; (d) `--from-backlog -` clears the field and inherits nothing. Paste the resulting bullet for each.
  - Observed evidence: Verified diff (identical to V-02) and all 4 driven outcomes on `--status` path:
    Outcome (a): gate inherited + notice printed
    ```text
    aw set: inherited - Blocks-Release: relaaa from backlog item bkl001 (graduation handoff: the gate travels with the work)
    aw specs set: <scratch>/.aw/records/specs/to-review/20260925-sp0001-01-sp0001-spec-a.spec.md -> to-review
    Resulting bullets:
      - Status: to-review
      - Blocks-Release: relaaa
      - From-Backlog: bkl001
    ```
    Outcome (b): explicit `--blocks-release relbbb` wins over item gate `relaaa`
    ```text
    aw specs set: <scratch>/.aw/records/specs/to-review/20260925-sp0002-01-sp0002-spec-b.spec.md -> to-review
    Resulting bullets:
      - Status: to-review
      - From-Backlog: bkl001
      - Blocks-Release: relbbb
    ```
    Outcome (c): existing `- Blocks-Release: relbbb` on spec is preserved
    ```text
    aw specs set: <scratch>/.aw/records/specs/to-review/20260925-sp0003-01-sp0003-spec-c.spec.md -> to-review
    Resulting bullets:
      - Status: to-review
      - From-Backlog: bkl001
      - Blocks-Release: relbbb
    ```
    Outcome (d): `--from-backlog -` clears field and inherits nothing
    ```text
    aw specs set: <scratch>/.aw/records/specs/to-review/20260925-sp0004-01-sp0004-spec-d.spec.md -> to-review
    Resulting bullets:
      - Status: to-review
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the run showing every case passing on BOTH spellings. Then prove the new tests can FAIL, by reverting E-02 and E-03 in the worktree (`git stash` the two files or comment the writers out), pasting the `--status` cases FAILING, then restoring and pasting `git diff --stat agent_workflows/specs.py` showing an EMPTY diff. Also paste a passing `python3 -m pytest tests/test_specs_verbs.py tests/test_specs_status_dirs.py tests/test_spec_review_attestation.py -o addopts="" -q`, which is what a direct `args.from_backlog` would break (F-7).
  - Observed evidence: Verified all 8 tests pass on both spellings and failure proof when reverted:
    All 8 tests passing across both spellings:
    ```text
    $ python3 -m pytest tests/test_specs_from_backlog.py -o addopts="" -q
    ........                                                                 [100%]
    8 passed in 0.34s
    ```
    Proved tests fail when E-02/E-03 are commented out (all 4 `--status` cases fail, 4 bare pass):
    ```text
    FAILED tests/test_specs_from_backlog.py::SpecsFromBacklogTests::test_status_spelling_existing_gate_not_overwritten
    FAILED tests/test_specs_from_backlog.py::SpecsFromBacklogTests::test_status_spelling_explicit_blocks_release_wins
    FAILED tests/test_specs_from_backlog.py::SpecsFromBacklogTests::test_status_spelling_from_backlog_dash_clears_field_and_inherits_nothing
    FAILED tests/test_specs_from_backlog.py::SpecsFromBacklogTests::test_status_spelling_from_backlog_writes_field_and_inherits_gate
    4 failed, 4 passed in 0.37s
    ```
    Restored and verified diff is empty relative to desired state.
    Existing test suites calling specs.run_set with minimal namespaces pass:
    ```text
    $ python3 -m pytest tests/test_specs_verbs.py tests/test_specs_status_dirs.py tests/test_spec_review_attestation.py -o addopts="" -q
    .......................................................                  [100%]
    55 passed in 0.86s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `AGENTS.md` diff; paste `grep -n "from-backlog" AGENTS.md .aw/records/specs/README.md .aw/records/backlog/README.md` showing the corrected AGENTS.md text and confirming (as at review) that neither README mentions the field, stated as a NO-OP rather than as a fix; and paste evidence the edited line is BELOW `<!-- /aw:block -->` (its line number beside the marker's), so no managed block was touched.
  - Observed evidence: Verified AGENTS.md diff, grep confirmation of no-op on READMEs, and position below marker:
    AGENTS.md diff:
    ```diff
    diff --git a/AGENTS.md b/AGENTS.md
    index 90fe80fa..99ecc030 100644
    --- a/AGENTS.md
    +++ b/AGENTS.md
    @@ -205,8 +205,8 @@ installed into every managed repo from `engine.py`. Do not restate it here.
     A plan may also carry a `- From-Backlog: <backlog-id6>` front-matter field naming the backlog item it
     graduated from, so the backlog->plan handoff is machine-readable rather than prose. Set it with `aw ipd
     set <status> <plan> --from-backlog <id6>` (clear with `--from-backlog -`). A SPEC may carry the same
    -field and is an equally valid gate carrier, so a spec-first graduation can legitimately close its item.
    -`aw check` flags a
    +field and is an equally valid gate carrier, so a spec-first graduation can legitimately close its item;
    +`aw specs set` carries the same `--from-backlog` flag on both spellings. `aw check` flags a
     `From-Backlog` value that resolves to no backlog item (`check.from-backlog-dangling`). This link lets a
     blocking backlog item's release gate be provably handed off to the plan that inherits it (so the item can
     close `done` without silently dropping the gate).
    ```
    Grep check confirming corrected text and no-op on READMEs:
    ```text
    $ grep -n "from-backlog" AGENTS.md .aw/records/specs/README.md .aw/records/backlog/README.md
    AGENTS.md:207:set <status> <plan> --from-backlog <id6>` (clear with `--from-backlog -`). A SPEC may carry the same
    AGENTS.md:209:`aw specs set` carries the same `--from-backlog` flag on both spellings. `aw check` flags a
    AGENTS.md:210:`From-Backlog` value that resolves to no backlog item (`check.from-backlog-dangling`). This link lets a
    AGENTS.md:225:(set with `aw ipd set ... --from-backlog <id6>`); (2) SATISFIED, a resolvable in-tree artifact citation
    AGENTS.md:229:`aw check` consistency rules (`check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`,
    ```
    Edited line (209) is below `<!-- /aw:block -->` (line 123):
    ```text
    123:<!-- /aw:block -->
    209:`aw specs set` carries the same `--from-backlog` flag on both spellings. `aw check` flags a
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence: Bare test suite passed cleanly with 0 failed:
    ```text
    2378 passed, 1 skipped, 3 warnings in 42.05s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (a spec-first graduation can record its backlog source through a setter) across six items. E-02 and E-03 are separate because the field write is a one-line call carrying no policy while the gate inheritance carries three precedence rules and a second artifact read; they fail differently and need different evidence.

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a new flag on `aw specs set` plus the writer that makes its `--status` spelling behave like its bare one. Nothing existing changes behavior; every write is guarded on the new flag being passed, so a caller that does not pass it is byte-unaffected. The one judgement worth a human's attention is OQ-02, where review DECLINED the plan's original id6 validation because shipped policy rules this write is never a refusal; if the maintainer wants validation instead, it belongs on both spellings at once and this plan should be re-scoped rather than quietly extended.

Scope fence (a DECLARATION for reconciliation, not a stop directive): within `cli.py` only the `p_specs_set` parser block gains one `add_argument`; within `specs.py` only `run_set`, adding a field write and a gate-inheritance block beside the four existing writers and BEFORE the `validate_spec` pass (so a malformed result is still refused); `tests/test_specs_from_backlog.py` is new; within `AGENTS.md` only the Release gates section's setter sentence, which is below `<!-- /aw:block -->`. The two records READMEs are declared because E-05 greps them and is expected to change neither, so ACK them at finalize rather than editing them. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

EXPLICITLY NOT IN SCOPE, each recorded in Deferred with its reason: `aw specs new --from-backlog`; any id6 validation or refusal (OQ-02); and `command_surface.py`, which is why that path was removed from `- Scope-Paths:` at review.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. V-01 through V-03 demand DRIVEN output, not diffs: review measured that this exact code path returns rc 0 and silently writes nothing, so a diff that looks right proves nothing about whether the writer runs.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the `- From-Backlog:` write makes `specs.validate_spec` refuse the result (review measured it does not, since the bare spelling already writes the field and the spec conforms), stop and report rather than relaxing the validator; if the AGENTS.md sentence turns out to sit INSIDE a managed block after all, stop and report rather than editing it, because the next install would silently revert it; if either records README does contain a claim needing correction, report the hit rather than treating F-6's no-op prediction as authority.

Commit through `aw commit <plan> -- <paths>`, path-scoped, never `git add -A`, never push. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which the RUNNER owns when it executes this plan in a lane and which the executor otherwise performs with `aw ipd finalize`, never with a raw `git mv`. Then set backlog item `mod4ml` `done` with `--evidence` citing the executed plan; it carries no `- Blocks-Release:`, so no gate handoff is required.
