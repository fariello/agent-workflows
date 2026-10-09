# IPD: Make aw specs set status a thin adapter delegating to the shared status set engine

- Date: 2026-10-01
- Kind: child
- Concern: `aw specs set` has two spellings reaching two separate implementations, and `specs.run_set` is the smaller of the two at roughly 330 lines against the shared engine's 1480. It re-implements status validation, the status write, relocation, history assembly and the self-commit offer, and it carries behaviors the shared engine lacks (a post-write `validate_spec` conformance refusal, a `--date` override, a sidecar append) while LACKING capabilities the shared engine has (selector resolution beyond a bare path, multi-selector batch, `--force`, the confirmation gate, structured agent/JSON output, auto-indexing). Spec `wy9aru` Section 4.1 rules the shared engine canonical and these per-verb functions thin adapters. Until that happens, every future gate on `aw specs set` must be written twice or it is bypassable, which is the recurring class backlog `fcnz1r` documents five instances of.
- Scope: IN: reduce `specs.run_set` to an argument-normalizing adapter that delegates to `status_set.run_set_command`, preserving its name and callable signature; carry its three genuinely-own behaviors into the shared engine as explicitly type-scoped parameters (the post-write `validate_spec` refusal, the `--date` override, the sidecar append); inherit the shared engine's selector vocabulary per `wy9aru` 4.5 and OQ-2; keep every refusal from both sides per `wy9aru` 4.7. OUT, each with a reason recorded under "Deferred": the backlog path (child 05); the two gate bypasses (child 03, which must land first); every axis `wy9aru` Section 7 assigns elsewhere; any change to what a spec status MEANS or to the transition table.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_specs_set_adapter.py, .aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md, CHANGELOG.md
- Item-Dependencies: executed:m1jlwm, executed:ulepef, state:spec:approved:wy9aru
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- From-Spec: wy9aru
- Set: setdisp
- Order: 4
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m94eht
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed
- 2026-10-07 /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (all fixed; record `.aw/records/reviews/20261001-setdisp-04-m94eht-make-aw-specs-set-status-a-thin-adapter-delegating-to-the-sh.review.md`). Execution remains gated on `wy9aru` reaching `approved` (its OQ-1 is BLOCKING on the maintainer) and on `ulepef` executing.
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: The bare suite pytest after the final child compared by name against baseline

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fcnz1r` under spec `wy9aru`. THIS PLAN IS GATED ON `wy9aru` OQ-1 (the sidecar ruling), which is BLOCKING on a maintainer call, and E-03 cannot be authored until that call is made: it implements whichever answer the maintainer gives. The two engines were read in full at HEAD `ec857565a` and the base suite measured bare (`3512 passed, 2 skipped`). This plan declares a SPEC EDIT (`1525-02`), announced per `AGENTS.md` because the sidecar's writer SITE moves.
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave `aw specs set` with ONE implementation of transition validation, the status write and
relocation, reached by both of its spellings, so that the next gate added to it is reachable from both
by construction rather than by remembering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: carry the specs-only behaviors into the shared engine first

- [x] E-01 Carry the post-write `validate_spec` CONFORMANCE REFUSAL into the shared engine, type-scoped to specs. `specs.run_set` validates the complete rendered result IN MEMORY and refuses BYTE-IDENTICALLY if it would not conform; the shared engine performs no such check, so the positional spelling can write a non-conforming spec.

    THIS IS THE THIRD `specs.run_set`-ONLY REFUSAL, and child 03 deliberately left it (that plan's F-06 records why: the other two are pre-write gates on specific transitions, while this one re-validates the whole result, so it is a different shape and did not belong in a measured two-bug fix). It belongs HERE, with the migration, because after delegation there is one write path and this refusal must guard it.

    IT MUST REMAIN A WRITE-NOTHING REFUSAL. The current behavior is that the file is left byte-identical when the rendered result would not conform. Preserving that exactly is the point: a refusal that leaves a half-written file is worse than no refusal, because the next reader cannot tell what happened.

    TYPE-SCOPE IT EXPLICITLY, not incidentally. The shared engine serves plans, specs, backlog items and prompts, and `validate_spec` applies to specs only. An unscoped call would run a spec validator over a plan.
  - Depends on: none
  - Expected outcome: a transition that would render a non-conforming spec is refused on BOTH spellings with a nonzero exit, the file left byte-identical and in its original directory; a transition over a non-spec record type is unaffected (demonstrate with a plan and a backlog item).
  - Execution state: performed

- [x] E-02 Carry the `--date` OVERRIDE into the shared engine, type-scoped to specs, preserving the UTC default. `specs.run_set` honors `--date` (`date = getattr(args, "date", None) or core.utc_history_date()`); the shared engine's `apply_status_change` stamps `_core.utc_history_date()` and honors no override, although `status_set`'s retry-flag table already lists `("date", "--date", True)`.

    THERE IS NO CLOCK CHANGE IN THIS PLAN (corrected at review 2026-10-07). As authored this item said `specs.run_set` stamps the LOCAL clock via `specs._today()` and that delegation would move it onto UTC. That stopped being true at commit `3c55295a3` (plan `5ivkdh`, "unify every artifact history date onto the UTC clock per spec 2vev8j 4.4"): `specs.run_set`, `backlog.run_set` and the shared engine all already stamp `utc_history_date()`, and `specs._today()` now survives only for `run_new`'s LOCAL filename prefix (DECISIONS.md D55). So delegation changes no clock, advances no clock carrier, and must not claim to.

    THE OVERRIDE STAYS A PLAIN PASS-THROUGH. `--date` exists so a migration or backfill can stamp a historical date; it is not a timezone control and must not acquire timezone semantics here.
  - Depends on: none
  - Expected outcome: `aw specs set <path> --status <s> --date 2020-01-01` writes `- 2020-01-01` in the new history record exactly as today; with no `--date`, the record carries the UTC date on both spellings, unchanged from before this plan; a non-spec type ignores the override exactly as today.
  - Execution state: performed

- [x] E-03 Implement the SIDECAR behavior the maintainer's answer to spec `wy9aru` OQ-1 selects. THIS ITEM CANNOT BE PERFORMED UNTIL THAT ANSWER EXISTS; it is the reason this plan is gated.

    IF OQ-1 RESOLVES TO "KEEP, TYPE-CONDITIONAL" (the spec's current ruling, 4.3): the shared engine appends exactly one `record_history.append_advisory` record for record types that have one today (`backlog`, `specs`) and none for the types that do not (`plans`, `prompts`, `research`), AFTER the durable write succeeds. The ordering half is NOT this plan's to decide: spec `2vev8j` C5 and AC-7 require it and plan `ulepef` already carries it, so `ulepef` MUST land first and this item adopts its ordering. Then AMEND `1525-02` R2 with a dated note recording that the writer site moved from `specs set`/`backlog set` to the shared engine while the REQUIREMENT is unchanged, in the style that spec already uses for its 2026-09-22 and 2026-09-28 amendments.

    IF OQ-1 RESOLVES TO "DROP": the shared engine appends no sidecar record for any type, `1525-02` R2 is amended from a MUST to a removal with the maintainer's reasoning recorded, `tests/test_history_provenance.py::test_backlog_set_appends_sidecar_and_preserves_inline` is deleted (it is an AC1 pin, so deleting it requires the amendment to land in the same change), and the fate of `aw record-history` is stated.

    DO NOT GUESS, AND DO NOT PROCEED ON THE SPEC'S CURRENT RULING AS IF IT WERE THE ANSWER. 4.3 is the author's recommendation and OQ-1 is marked BLOCKING precisely because it turns on whether anyone uses `aw record-history`, which is a maintainer's knowledge and not inferable from the tree. If the answer has not arrived when this plan is executed, STOP at this item, complete every independent item around it, and report the block.
  - Depends on: E-01
  - Expected outcome: whichever branch the maintainer selected is implemented, the `1525-02` amendment landed in the SAME change as the behavior, and the sidecar state after both spellings measured and pasted (one record each, or none each, matching the ruling).
  - Execution state: performed

### Task group 2: the delegation itself

- [x] E-07 SPIKE, BEFORE THE ADAPTER: measure every observable the delegation would change, and decide each one. Added at review because three were MEASURED to break callers the plan said would keep working unchanged (`.aw/records/reviews/20261001-setdisp-04-m94eht-make-aw-specs-set-status-a-thin-adapter-delegating-to-the-sh.review.md`, round 1).

    (a) FIXTURE-SHAPE REACHABILITY. `tests/test_specs_verbs.py` `SetTests._mk` writes a bare `s.md` into a `TemporaryDirectory` that is not a repository. MEASURED at review: `specs.run_set` transitions it (rc 0), but `status_set.run_set_command(["to-review", <that path>], scoped_type="specs", repo_root=<its dir>)` returns rc 2 `No specs artifact matched`, and with `repo_root` left to default (cwd) and a spec under another tmp repo it RAISES `ValueError ... is not in the subpath of` from `apply_status_change`'s `rec.path.relative_to(repo_root)`. Drive the shared engine with each `Namespace` shape used by the six direct-caller modules (the five named in F-03 plus `tests/test_specs_date_containment.py`) and record, per shape, whether it resolves. For each that does not, the fix must keep ONE engine: either make the shared resolver accept an explicit existing file path for a scoped verb (and pass `repo_root=specs._repo_root_of(path)` from the adapter, never cwd), or move that fixture into a records tree as a declared test edit. A fallback inside the adapter that calls the old code is FORBIDDEN, since it would be the fork this Set removes.

    (b) THE REFUSAL TABLE. For every refusal `specs.run_set` performs today (unknown status, no `- Status:` bullet, illegal transition, human-only, evidence, `->reviewed` attestation, `approval_refusals`, handoff, deferred gate pair, `--gate-summary`, `--message`, `--blocks-release`, `--graduated-to`, unresolvable `--from-backlog`, the `validate_spec` result check), record the rc and message on BOTH spellings before any edit. MEASURED at review: `--message 'a\nb'` is rc 1 `aw specs set: --message must not contain embedded newlines` on the `--status` spelling and rc 2 `aw set: --message ...` on the positional one. Each row must end as `preserved` (same rc and prefix after delegation) or `changed` (named in the CHANGELOG in E-06 and, if a test pins it, that test edited in the same change). Pinned today: `tests/test_specs_releases_descriptive_safety.py` (`aw specs set: --gate-summary ...` rc 1, `aw specs set: --graduated-to ...` rc 2), `tests/test_set_dispatch_dedup.py` and `tests/test_releases_line_writers.py` (`aw specs set: inherited - Blocks-Release:`). A refusal present only in `specs.run_set` that the engine lacks (per `wy9aru` 4.7) is carried, type-scoped, as E-01 does for `validate_spec`.

    (c) THE RECORDED ACTOR. `specs.run_set` writes `(aw specs)` / `(aw specs, --by-human)`; the shared engine writes `(aw set)` unless `args.actor` is set, and 36 assertions in nine test modules pin `(aw specs`. MEASURED at review: `run_set_command(..., args=Namespace(actor="aw specs", ...))` writes `- <date> to-review (aw specs): m`, and `attention_contract.actor_refusal("aw specs")` is `None`. So the adapter sets `actor="aw specs"` when the caller gave none, which PRESERVES the observed value rather than choosing a new one (`wy9aru` 4.6, `jbipfa`); record the before and after.
  - Depends on: none
  - Expected outcome: a pasted per-shape reachability table, a pasted refusal table with every row `preserved` or `changed`, the actor read back after delegation equal to the actor before it, and for each `changed` row the test path that pins it; E-04 does not start until every row is decided.
  - Execution state: performed

- [x] E-04 Reduce `specs.run_set` to an adapter: normalize its arguments and delegate to `status_set.run_set_command` with `scoped_type="specs"`. KEEP ITS NAME AND CALLABLE SIGNATURE (spec `wy9aru` S2): roughly twenty tests construct its `argparse.Namespace` by hand, so renaming it converts a behavior change into a mass test rewrite that would hide the behavior change inside the diff.

    THE ADAPTER'S WHOLE JOB IS ARGUMENT SHAPE, and two details decide whether it is correct. FIRST, `cli.main` currently MUTATES `args` before calling (`args.path = args.args[0] if args.args else args.path`), so the adapter must accept BOTH the `path` attribute its hand-built-Namespace callers set and the `args` list the CLI supplies. SECOND, the shared engine takes selector TOKENS, not a path, so the adapter passes the path as a selector; the shared engine's resolver accepts a path, which is what makes this work at all. Verify that rather than assuming it.

    PER `wy9aru` 4.5 AND OQ-2, THE `--status` SPELLING INHERITS THE SHARED SELECTOR VOCABULARY, so it begins accepting an id6 or a setid where it accepted a bare path. OQ-2 is NON-BLOCKING and recommends proceeding, on the ground that the positional spelling ALREADY accepts those selectors for specs, so the capability is reachable today by typing the other spelling and withholding it from one preserves exactly the false expectation this Set exists to remove. A SETID selector can transition SEVERAL specs in one call; the shared engine's all-or-nothing pre-flight and its confirmation gate both apply, which is what makes that acceptable. State this in the CHANGELOG as a user-visible widening.

    THE CONFIRMATION GATE NOW APPLIES TO THE `--status` SPELLING, which today has none. The shared engine requires `--yes` for agent/JSON callers and returns 2 otherwise. MEASURED at review: `aw specs set <path> --status to-review --agent` is rc 0 and writes today, while `aw specs set to-review abc123 --agent` is rc 2 `confirmation required`. That is a BEHAVIOR CHANGE for an `--agent`/`--json` caller of the `--status` spelling; OQ-02 records that no in-tree caller makes it, and the executor re-runs that search.

    THE ADAPTER APPLIES E-07's DECISIONS: `repo_root` derived from the spec path, `actor="aw specs"` when none was given, and every `preserved` row of the refusal table kept preserved.
  - Depends on: E-01, E-02, E-03, E-07
  - Expected outcome: `specs.run_set` contains no status validation, no status write, no relocation and no history assembly of its own; both spellings of `aw specs set` produce identical observable results on every axis the differential harness pins; every existing hand-built-Namespace caller still works unchanged; the measured list of newly-applying behaviors (confirmation gate, selector widening, structured output, auto-indexing) is recorded.
  - Execution state: performed

### Task group 3: prove it and record it

- [x] E-05 Author `tests/test_specs_set_adapter.py` and re-run the differential harness. The harness from child 02 (`tests/test_set_dispatch_parity.py`) is the primary evidence: every specs AGREEMENT assertion in it must still pass unchanged, which is what makes "behavior preserving" a measurement rather than a claim. Additionally FLIP the expected-difference assertions this plan closes: the `specs set --status` path-only selector limitation (`wy9aru` OQ-2) and, if OQ-1 resolved to keep, nothing in the sidecar row; state explicitly which expected-difference assertions were flipped and leave the rest alone.

    The NEW module covers what the harness does not: that `specs.run_set` is still callable with each hand-built `Namespace` shape its existing tests use (drive it directly, asserting outcomes); that the `--date` override still works; that the `validate_spec` refusal leaves the file byte-identical; and that the newly-applying confirmation gate behaves as the shared engine's contract states (rc 2 for an agent/JSON caller without `--yes`).

    NO TEST MAY READ PRODUCTION SOURCE with `inspect`/`ast`/regex, count callers, or assert docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). "There is now one implementation" must be proven by identical observable behavior across both spellings, never by a symbol census. Pass `--no-commit` on every CLI invocation.
  - Depends on: E-04
  - Expected outcome: every specs agreement assertion in `tests/test_set_dispatch_parity.py` passing unchanged; the flipped expected-difference assertions named individually with their new values; the new module's cases passing; the full bare suite's failure set unchanged except for tests this plan names.
  - Execution state: performed

- [x] E-06 Record the user-visible changes in `CHANGELOG.md` and reconcile the records. The entry must name what a USER can observe: `aw specs set --status` now accepts the same selectors as the positional spelling (an id6 or a setid, not only a file path); it now requires `--yes` for machine-readable callers; and it now refuses a transition that would render a non-conforming spec. Write no em or en dashes (user-facing prose, `AGENTS.md`), and do not describe the delegation itself, which a user cannot see.

    ALSO NAME every E-07 refusal-table row marked `changed` (a different exit code or message prefix is user-visible). Do NOT mention a clock change: there is none (E-02), and no clock carrier (`2wae2x`, `fnb8pl`, `lq2w86`) is touched by this plan.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-07
  - Expected outcome: one CHANGELOG entry naming the three user-visible changes plus each `changed` refusal row and nothing else, with no em or en dash; no clock carrier's status changed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This matters acutely here: `status_set.py` is 2785 lines and three other live plans edit it.
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). Unification is proven by identical observable behavior across both spellings, never by asserting that one implementation exists.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (`AGENTS.md`). This plan declares `1525-02` in `Scope-Paths`, so both runners announce the declared spec edit before the run starts and reconcile it at finalize. The amendment's REASON is in "Spec / documentation sync".
- `specs.run_set` is reached by roughly twenty tests via hand-built `argparse.Namespace` objects with exact field sets. Its signature is therefore a de facto internal contract, which is why `wy9aru` S2 forbids renaming it.
- `runner_shared.close_backlog_item` documents that it uses the `--status` spelling specifically because only that spelling honors `--gate-dir`. That constrains child 05, not this plan (specs have no `--gate-dir`), but it is the reason the adapters must keep working rather than being deleted.

## Findings

Established by reading `specs.run_set` and the shared engine in full at HEAD `ec857565a`, and by the measurements child 03 recorded.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (GATE) | Spec `wy9aru` OQ-1 is marked `Blocking: yes`, owner maintainer. Its subject is whether the sidecar write survives unification as a type conditional or is dropped. `1525-02` R2 is a MUST naming `specs set` and `backlog set`, pinned by `tests/test_history_provenance.py::test_backlog_set_appends_sidecar_and_preserves_inline`. | **THIS PLAN CANNOT BE FULLY EXECUTED UNTIL A MAINTAINER ANSWERS OQ-1**, and that is a feature of the decomposition rather than a defect in it. E-03 implements either answer and refuses to guess. The answer turns on whether anyone uses `aw record-history`, which is not inferable from the tree. Children 01, 02 and 03 were deliberately made independent of it so the Set makes real progress meanwhile. |
| F-02 | MEDIUM (ORDERING) | Plan `ulepef` (`approved` at review 2026-10-07, `Blocks-Release: next`; now carried as `executed:ulepef` in `- Item-Dependencies:` so the order is enforced by the runner, not by prose) moves the sidecar append AFTER the durable write in `backlog.run_set`, `backlog.run_note`, `specs.run_set` and `specs.run_note`, and ALREADY declares the `2vev8j` amendment in its own `Scope-Paths`. Its Scope OUT explicitly assigns the `status_set` sidecar asymmetry to `fcnz1r`. | **`ulepef` MUST LAND FIRST AND THE TWO PLANS AGREE ON THE BOUNDARY.** It owns the ORDERING (append after the durable write, per `2vev8j` C5); this plan owns the SITE (which function appends). Landing this first would move a write site whose ordering is about to be corrected, forcing `ulepef` to be rewritten against a function that no longer exists. The two plans already cite each other's boundary, which is evidence the split is real rather than asserted. |
| F-03 | MEDIUM (SIGNATURE CONTRACT) | `specs.run_set` is called directly by roughly twenty tests across `tests/test_specs_verbs.py` (thirteen calls), `tests/test_specs_status_dirs.py`, `tests/test_specs_from_backlog.py`, `tests/test_spec_review_attestation.py` and `tests/test_stdin_interactive.py`, each with a hand-built `Namespace`. | **THE FUNCTION'S SIGNATURE IS A DE FACTO CONTRACT WITH THE TEST SUITE**, so `wy9aru` S2's prohibition on renaming is load-bearing rather than stylistic. Keeping the name turns a twenty-file test rewrite into a no-op and keeps the diff reviewable, which is exactly what a migration of this size needs. |
| F-04 | MEDIUM (BEHAVIOR CHANGE) | The shared engine requires `--yes` for agent/JSON callers and returns 2 otherwise; `specs.run_set` has no confirmation concept. | **DELEGATION MAKES THE CONFIRMATION GATE APPLY TO A SPELLING THAT NEVER HAD ONE**, which can break automation calling `aw specs set --status` with `--agent` and no `--yes`. This is the one behavior change of the delegation that can fail a caller rather than merely widening what it accepts, so E-04 requires measuring whether anything in-tree makes that call before assuming nothing does. |
| F-05 | LOW (CLOCK, CORRECTED AT REVIEW) | Commit `3c55295a3` (plan `5ivkdh`): `specs.run_set` `date = getattr(args, "date", None) or core.utc_history_date()`; `backlog.run_set` the same; `status_set.apply_status_change` `today = _core.utc_history_date()`. `specs._today()` is now used only by `run_new` for the LOCAL filename prefix (D55). | **THERE IS NO CLOCK AXIS LEFT ON THIS PATH.** As authored this row said delegation would move the specs path from the local clock to UTC; that was true at `ec857565a` and was fixed by `5ivkdh` before review. E-02 is reduced to the `--date` pass-through and E-06 must not claim a clock consequence. |
| F-06 | MEDIUM (WIDENING) | `specs.run_set` resolves its target with `Path(args.path)` and consults no selector resolver. The shared engine resolves id6, setid, status, stem, substring and path. | **THE `--status` SPELLING GAINS SELECTOR CAPABILITY, INCLUDING SETID, WHICH CAN TRANSITION SEVERAL SPECS AT ONCE.** `wy9aru` OQ-2 is non-blocking and recommends accepting it, because the positional spelling already offers those selectors so the capability is reachable today. The shared engine's all-or-nothing pre-flight and confirmation gate are what make a multi-spec transition acceptable; both apply after delegation. User-visible, so E-06 puts it in the CHANGELOG. |
| F-07 | LOW (SCOPE RECEIVED) | Child 03's F-06 defers the post-write `validate_spec` refusal to this plan, naming it as a different shape from the two pre-write gates it fixes. | **THIS PLAN RECEIVES EXACTLY ONE DEFERRED OBLIGATION FROM CHILD 03 AND E-01 DISCHARGES IT.** Worth stating because an unowned deferral is how a refusal silently disappears during a migration: after delegation there is one write path, and if nothing guards it, the conformance refusal is simply gone. |
| F-10 | HIGH (MEASURED AT REVIEW: CALLER-BREAKING CHANGES THE PLAN DID NOT NAME) | Scratch probes with the lane package pinned (`PYTHONPATH`, `AW_NO_REEXEC=1`): bare `s.md` outside a repository, `--status` spelling rc 0 vs shared engine rc 2 `No specs artifact matched`; defaulted `repo_root` with a spec in another tmp repo raises `ValueError` from `apply_status_change`; actor `(aw specs)` vs `(aw set)` (36 pinned assertions in nine modules); `--message 'a\nb'` rc 1 `aw specs set:` vs rc 2 `aw set:`. | **E-04's expected outcome ("every existing hand-built-Namespace caller still works unchanged") WAS NOT REACHABLE AS WRITTEN.** E-07 is added as a spike that measures and decides each observable before the adapter is written, and E-04 now consumes those decisions. |
| F-08 | N/A (BASELINE) | `python3 -m pytest` at HEAD `ec857565a`: `3512 passed, 2 skipped, 3 warnings in 111.12s (0:01:51)`. | **THE BASE IS GREEN AT THIS HEAD AND THAT IS TIME-DEPENDENT** (one existing cross-spelling test is red whenever local and UTC dates differ). RE-DERIVE and compare failure SETS BY NAME, never against this count. |
| F-09 | LOW (WAS HIGH; RESOLVED BEFORE REVIEW) | RE-MEASURED AT REVIEW 2026-10-07 with this plan's edge present: `python3 -m pytest tests/test_terminal_status_vocabulary.py -o addopts="" -q -k blast_radius` -> `1 passed`; `pyhq6s` is `graduated`. Original authoring evidence: with this plan's `- Item-Dependencies: executed:m1jlwm, state:spec:approved:wy9aru` present, the bare suite reports `1 failed, 3511 passed`, the failure being `tests/test_terminal_status_vocabulary.py::TestExecutionSuccessStatesNarrowingAndBlastRadius::test_blast_radius_zero_across_pending_plans` with `stranded prerequisites: [('...m94eht...', 'wy9aru')]`. The edge was then verified legal three ways: `ipd_schema.parse_item_dependencies` parses it to `ItemDependency(kind='state', target_type='spec', status='approved', id6='wy9aru')`; `runner_shared.preflight_dependency_findings` reports NO findings; and `runner_shared.edge_satisfied` returns `(False, "state:spec:approved:wy9aru: spec wy9aru is 'to-review', needs exactly 'approved'")`. | **THE SUITE IS NO LONGER RED ON THIS EDGE (review); THE ORIGINAL DIAGNOSIS STANDS AS HISTORY.** THE DEPENDENCY GATE ON THIS PLAN IS REAL AND ENFORCED; THE FAILING TEST WAS A PRE-EXISTING DEFECT THIS PLAN IS THE FIRST TO EXPOSE.** That test globs only the plans trees for every dependency id6 (its own comment says "Strip any prefix like `ipd:`", from when only ipd edges existed), while a `spec`/`backlog` target is DELIBERATELY a graph LEAF resolved against the repository, as `validate_manifest` states in so many words. So it asserts an invariant the design contradicts, and no plan can use the shipped `spec`/`backlog` edge grammar without turning the suite red. THE TRAP IT SETS IS THE REASON THIS ROW IS HIGH: the failure names the authoring PLAN, so an author concludes their own legal edge is malformed and deletes it, which here would remove the only thing stopping this plan from executing before the maintainer answers a blocking question. FILED as `pyhq6s` with the measurement and a suggested fix (parse the token, resolve a non-ipd target against its own tree); NOT fixed here, because it is a test-correctness bug in another module with its own blast radius. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/status_set.py`: the post-write `validate_spec` conformance refusal, type-scoped to specs (E-01).
2. `agent_workflows/status_set.py`: the `--date` override, type-scoped to specs, UTC default preserved (E-02).
3. `agent_workflows/status_set.py` + `.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md`: whichever sidecar behavior `wy9aru` OQ-1 selects, with the matching R2 amendment in the SAME change (E-03).
3a. No production file: the E-07 spike measures fixture-shape reachability, the refusal table and the recorded actor on both spellings and decides each row before any adapter edit (E-07).
4. `agent_workflows/specs.py` + `agent_workflows/cli.py`: `specs.run_set` becomes an argument-normalizing adapter delegating to the shared engine; `cli.main`'s `args` mutation is reconciled with it (E-04).
5. `tests/test_specs_set_adapter.py`: the adapter's own cases; plus the child 02 harness re-run with its flipped expected-difference assertions named (E-05).
6. `CHANGELOG.md`: one entry naming the three user-visible changes (E-06).

## Deferred / out of scope (with reason)

- THE BACKLOG PATH IS NOT MIGRATED HERE. Spec `wy9aru` S4 requires the migration to be INCREMENTAL AND PER-VERB, never one commit, each with its differential harness green before the next starts. Specs is the smaller and simpler of the two (no `--gate-dir`, no `_render_item` round trip, no `git_mv`-versus-unlink divergence), so it goes first and de-risks the larger one.
  - Carrier: vhiqo6
- THE TWO MEASURED GATE BYPASSES ARE NOT FIXED HERE. They are release-gated bugs that must ship without waiting on `wy9aru` OQ-1, which is why child 03 fixes them across the existing fork and this plan depends on it having executed.
  - Carrier: m1jlwm
  - Carrier-Evidence: .aw/records/plans/executed/20261001-setdisp-03-m1jlwm-close-the-two-measured-positional-specs-set-gate-bypasses-by.ipd.md
- THIS PLAN'S OWN `state:spec:approved:wy9aru` EDGE TURNED THE SUITE RED AT AUTHORING TIME (F-09); at review the test passes with the edge present and `pyhq6s` is `graduated`. Do NOT delete or weaken the edge in any case: it is the only thing preventing this plan from executing before a maintainer answers a BLOCKING spec question.
  - Carrier: pyhq6s
- NO CLOCK WORK (F-05, corrected at review). Every writer on this path already stamps UTC since `5ivkdh`; this plan neither advances nor closes a clock carrier, and any remaining clock item is owned where it is filed.
  - Carrier: 2wae2x
- THE HISTORY LABEL, THE SAME-STATUS DEDUP, THE DEFAULTED MESSAGE AND THE DEAD `apply` READ are all untouched and normalized around, each owned elsewhere per `wy9aru` Section 7.
  - Carrier-Evidence: .aw/records/specs/approved/20261001-wy9aru-01-wy9aru-canonical-set-dispatch.spec.md
- THE ACTOR STRING IS NOT UNIFIED. `jbipfa` declines actor unification as truthful attribution, so this plan PRESERVES the observed `(aw specs)` actor by passing the engine's existing `actor` parameter (E-07 (c)) rather than letting it silently become `(aw set)` or choosing a new value.
  - Carrier-Declined: declined in `jbipfa` as not-a-defect; this plan records the observed value rather than selecting one, so there is no outstanding work
- `aw prompts set` registration is not this plan's concern. Its carrier `68sur3` is `done` at review (closed by executed plan `gm9baj`); recorded only so a reader of `wy9aru` Section 7 does not look for it here.
  - Carrier: 68sur3

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/status_set.py` (E-01, E-02, E-03), `agent_workflows/specs.py` (E-04, applying E-07's decisions), `agent_workflows/cli.py` (E-04), `tests/test_specs_set_adapter.py` (E-05), the `1525-02` spec (E-03), `CHANGELOG.md` (E-06).
- Under-scope: E-05 re-runs and FLIPS assertions in `tests/test_set_dispatch_parity.py`, which child 02 authors and which is therefore not declared here; the flip is a one-value edit per closed axis and the file is undeclared because declaring another plan's file invites a scope-reconciliation conflict. Declare it at execution if the finalize scope gate requires it and record the widening in the transition message; this note is the authorization. E-03 may also delete `tests/test_history_provenance.py::test_backlog_set_appends_sidecar_and_preserves_inline` if OQ-1 resolves to DROP; that path is likewise undeclared because the branch is not yet known. E-07 (b) may also edit `tests/test_specs_releases_descriptive_safety.py`, `tests/test_set_dispatch_dedup.py`, `tests/test_releases_line_writers.py`, and E-07 (a) a direct-caller module's fixture, ONLY for a row E-07 marks `changed`; each is undeclared because whether it is touched depends on the measurement, and finalize's `--scope-reason` per path records the justification. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline before any edit and compare FAILURE SETS BY NAME, not counts (F-08).
- `tests/test_set_dispatch_parity.py` (child 02's harness) run alone under BOTH the machine's local timezone and `TZ=UTC`, with every specs AGREEMENT assertion shown passing UNCHANGED. This is the primary evidence that the migration is behavior-preserving; a changed agreement assertion is a regression unless this plan named it in advance.
- The new `tests/test_specs_set_adapter.py` run alone with `-o addopts=""`, every case named.
- The six existing modules that call `specs.run_set` directly (`tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_specs_from_backlog.py`, `tests/test_spec_review_attestation.py`, `tests/test_stdin_interactive.py`, `tests/test_specs_date_containment.py`), each run individually with its result pasted, proving the preserved signature.
- A direct measurement of the sidecar state after BOTH spellings, pasted, matching whichever branch of E-03 was implemented.
- `AW_NO_REEXEC=1 aw specs check` and `AW_NO_REEXEC=1 aw sanitize --agent`, each expected to exit 0.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: BOTH exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET, not an exit code. Re-derive before and after. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing. Per `wy9aru` S5, the spec amendment and the behavior it describes land in the SAME commit, and no commit may both unify a path and fix an axis Section 7 defers.

## Spec / documentation sync

THIS PLAN AMENDS AN `implemented` SPEC AND THE AMENDMENT IS DECLARED IN `Scope-Paths`, so both runners
announce it before the run starts and reconcile it at finalize (`AGENTS.md`).

`.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md` R2 is a MUST that
routes "the specs + backlog status-transition writers (`specs set`, `specs note`, `backlog set`,
`backlog note`)" to append a sidecar record. After E-03 and E-04 the WRITER IS THE SHARED ENGINE,
conditioned on record type, so the requirement's SITE moves while (under the KEEP branch) the
requirement itself is unchanged. R2 therefore takes a dated amendment note in the style that spec
already uses for its 2026-09-22 and 2026-09-28 amendments. WHY THIS MATTERS ENOUGH TO EDIT AN
`implemented` SPEC: leaving R2 naming functions that no longer perform the write would make the spec
describe a routing that does not exist, and the next reader tracing provenance would conclude the
requirement had been dropped.

If OQ-1 resolves to DROP, the amendment is larger: R2 changes from a MUST to a removal, carrying the
maintainer's reasoning and the consequence for `aw record-history`. E-03 covers both branches.

Spec `wy9aru` (`to-review`) governs this Set and is NOT edited: this plan implements its 4.1, 4.5 and
4.7 and answers nothing on its behalf. `0151-01` names `specs.run_set` by symbol as the `--by-human`
attestation site; that attestation is already duplicated into the shared engine so the CONTRACT is
intact and only the cited location moves. Whether to re-cite it there is a judgement; record the
decision in the final report rather than editing a second `implemented` spec inside a migration.

## Open questions

### OQ-01: which sidecar behavior does E-03 implement, given spec `wy9aru` OQ-1?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AS A DEPENDENCY RATHER THAN AS AN OPEN QUESTION, which is the correct mechanism and not a downgrade of the gate. The underlying question (sidecar kept type-conditionally, or dropped) is owned by spec `wy9aru` OQ-1 and is BLOCKING THERE, where it belongs; duplicating it here would mean two artifacts asserting ownership of one maintainer decision, and the plan's copy could be marked resolved while the spec's stayed open. Instead this plan carries `- Item-Dependencies: state:spec:approved:wy9aru`, so it is MECHANICALLY INELIGIBLE to execute until that spec reaches `approved`, which is the transition that requires the maintainer to have answered its own blocking question. The gate is therefore enforced by the runner's dependency check rather than by an executor remembering to read this section. E-03 implements whichever branch the approved spec states and must not guess; if the spec is approved with OQ-1 still unanswered, STOP at E-03, complete every independent item, and report the block.

### OQ-02: does anything in-tree call `aw specs set --status` with `--agent` or `--json` and without `--yes`?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-10-07 FROM A TREE SEARCH: no production module, host runner or workflow body invokes `aw specs set ... --status` with `--agent` or `--json` (`agent_workflows/runner_shared.py` names only the positional `aw specs set <status> <id6>` spelling; `engine.py`'s managed AGENTS block advertises `aw specs set <path> --status approved --by-human --message ...`, which passes neither flag; the only test argv pairing `specs set` with `--status` and those flags is in `tests/test_completion.py`, which exercises shell completion, not dispatch). So no in-tree caller needs updating in the same change; E-04 re-runs the search at execution and records it, and the CHANGELOG still names the new `--yes` requirement because an out-of-tree script may make that call. Original rationale: F-04 establishes that delegation makes the shared engine's confirmation gate apply to a spelling that has none today, returning 2 for a machine-readable caller without `--yes`. This is the delegation's only change that can FAIL an existing caller rather than widening what it accepts. Answerable by searching the tree (including `runner_shared`, the hosts, and the workflow bodies) at execution time. It cannot change the design, since the gate is the shared engine's documented contract; it changes only whether a caller must be updated in the same change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted rc and the file read back for a transition that would render a NON-CONFORMING spec, on both spellings, showing the file byte-identical and in its original directory (paste a checksum or the full text before and after); plus a demonstration over a PLAN and a BACKLOG item showing the spec validator did not run on them.
  - Observed evidence:
    Transition over non-conforming spec (duplicate metadata bullet `- Title:`):
    Flag spelling:
    $ aw specs set .aw/records/specs/draft/20261001-s1-01-sp0001-test.spec.md --status to-review --no-commit
    aw specs set: the resulting spec would not conform; refused (file unchanged):
      spec.metadata-bullet-repeated: metadata bullet - Title: appears 2 times
    rc=1, byte_identical=True, path=.aw/records/specs/draft/20261001-s1-01-sp0001-test.spec.md

    Positional spelling:
    $ aw specs set to-review sp0001 --no-commit
    aw specs set: the resulting spec would not conform; refused (file unchanged):
      spec.metadata-bullet-repeated: metadata bullet - Title: appears 2 times
    rc=1, byte_identical=True, path=.aw/records/specs/draft/20261001-s1-01-sp0001-test.spec.md

    Demonstration over plan (duplicate Title bullet, validator does not run):
    $ aw ipd set approved pl0001 --no-commit --yes
    -    plan        20261001-s1-01-pl0001  [low]  pending → ◕  approved
    rc=0

    Demonstration over backlog item (duplicate Title bullet, validator does not run):
    $ aw backlog set parked bk0001 --no-commit --yes
    -    backlog     20261001-bk0001-01-bk0001  open → ◇  parked
    rc=0
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted history record written by `aw specs set <path> --status <s> --date 2020-01-01` showing `- 2020-01-01`; the record written with no `--date` on BOTH spellings showing the same UTC date (run once under a `TZ` whose local date differs from UTC at run time, so agreement is not coincidental); and the `- Status:` of `2wae2x`, `fnb8pl` and `lq2w86` before and after, unchanged.
  - Observed evidence:
    History record with --date 2020-01-01:
    - 2020-01-01 to-review (aw specs): status set to to-review

    Record written with no --date under TZ=Pacific/Kiritimati (UTC+14):
    Flag spelling:
    - 2026-10-09 to-review (aw specs): status set to to-review
    Positional spelling:
    - 2026-10-09 to-review (aw set): status set to to-review
    (Both stamp UTC date 2026-10-09).

    Status of clock carriers before and after (unchanged):
    .aw/records/backlog/done/20260930-2wae2x-01-2wae2x-backlog-status-set-tz-parity.backlog.md: - Status: done
    .aw/records/backlog/done/20260930-fnb8pl-01-fnb8pl-unify-the-history-date-clock-across-both-backlog-s.backlog.md: - Status: done
    .aw/records/backlog/done/20260930-lq2w86-01-lq2w86-fix-date-timezone-parity-between-backlog-run-set-a.backlog.md: - Status: done
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the maintainer's answer to `wy9aru` OQ-1 quoted with its source; pasted `record_history` read-back after a transition through EACH spelling, matching the selected branch (one record each, or none each); and the diff of the `1525-02` R2 amendment, landed in the same change as the behavior.
  - Observed evidence:
    Maintainer's resolution quoted from spec wy9aru Section 6 OQ-1:
    "DECIDED BY THE MAINTAINER, 2026-10-08, interactively during /spec-review: KEEP THE SIDECAR, TYPE-CONDITIONAL (`backlog` and `specs` only), as 4.3 rules. The maintainer was told the sidecar is gitignored, does not survive a clone, held 341 lines in this checkout, is read by `aw record-history`, and duplicates what the inline `## Workflow history` already records durably; and that dropping it would delete a shipped verb and require amending `1525-02` R2. No `1525-02` requirement changes; only its writer SITE moves (Section 6). Unblocks plan `m94eht` (Set `setdisp` Order 04) E-03 on its 'KEEP, TYPE-CONDITIONAL' branch."

    Pasted record_history.read_all(repo_root) read-back after transition through each spelling:
    After flag spelling:
    {'id6': 'sp0001', 'date': '20261009', 'tree': 'specs', 'workflow': 'aw specs', 'actor': 'aw specs', 'message': 'to-review: status set to to-review'}
    After positional spelling:
    {'id6': 'sp0002', 'date': '20261009', 'tree': 'specs', 'workflow': 'aw specs', 'actor': 'aw specs', 'message': 'to-review: status set to to-review'}
    (Exactly one advisory record per transition).

    1525-02 R2 amendment diff:
    ```diff
    --- a/.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md
    +++ b/.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md
    @@ -9,6 +9,7 @@
     ## Workflow history
    +- 2026-10-09 note (aw specs): AMENDED by plan m94eht (setdisp Order 04): Section 4 R2 amended with dated note recording that the writer site for specs moved from specs set to the shared status set engine (status_set.apply_status_change) under spec wy9aru Section 4.3, while the sidecar requirement is unchanged.
     - 2026-09-30 note (aw specs): AMENDED by plan eikajx: Section 3, R3, R4 and AC2 amended to reflect machine-local sidecar and durable inline history; AC1 citations updated
    @@ -62,6 +63,7 @@ Key flow: state stays inline (cheap, always-needed); the growing narrative lives
     - R1 (MUST). Define the sidecar schema + location (Section 3: `.aw/records/history.jsonl`, line `{id6,date,tree,workflow,actor,message}`) and an append/read module `record_history.py`.
     - R2 (MUST). Route the specs + backlog status-transition writers (`specs set`, `specs note`, `backlog set`, `backlog note`) to ALSO append one sidecar history record, and PRESERVE the full inline `## Workflow history`, newest-first.
       **AMENDED 2026-09-22 (maintainer ruling 2026-09-10, plan `vhbvwz` OQ-01 / E-08).** ...
    +  **AMENDED 2026-10-09 (plan `m94eht`, Set `setdisp` Order 04).** As part of migrating `aw specs set` onto the shared status set engine (`status_set.apply_status_change`) per spec `wy9aru` Section 4.3, the writer site for specs transitions moved from `specs.py:run_set` to `status_set.py:apply_status_change` (type-conditional: `specs` and `backlog` only). The sidecar append requirement is unchanged.
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted individual results for the six existing modules that call `specs.run_set` directly, proving the signature survived; pasted side-by-side output of both spellings over an identical fixture showing identical status, location and record; the answer to OQ-02 with the search that produced it; and the enumerated list of newly-applying behaviors (confirmation gate, selector widening, structured output, auto-indexing) each demonstrated once.
  - Observed evidence:
    Individual test runs for the 6 direct-caller modules:
    - tests/test_specs_verbs.py: 20 passed in 2.13s
    - tests/test_specs_status_dirs.py: 8 passed in 2.12s
    - tests/test_specs_from_backlog.py: 8 passed in 2.16s
    - tests/test_spec_review_attestation.py: 30 passed in 2.42s
    - tests/test_stdin_interactive.py: 5 passed in 2.04s
    - tests/test_specs_date_containment.py: 15 passed in 2.67s

    Side-by-side output over identical fixture:
    Flag spelling:       rc=0, location=to-review, history=- 2026-10-09 to-review (aw specs): status set to to-review
    Positional spelling: rc=0, location=to-review, history=- 2026-10-09 to-review (aw set): status set to to-review

    OQ-02 tree search result:
    `git grep "specs set.*--status.*--\(agent\|json\)"` produced only plan and review narrative records; no production caller, host runner, or workflow body invokes `aw specs set ... --status` with `--agent` or `--json`.

    Newly-applying behaviors demonstrated:
    1. Confirmation gate: `aw specs set <path> --status to-review --agent` returns rc=2 with "confirmation required" unless `--yes` is passed.
    2. Selector widening: `aw specs set sp0001 --status to-review --yes` resolves id6 selector and succeeds (rc=0).
    3. Structured output: `aw specs set <path> --status to-review --agent --yes` emits canonical `aw.agent/v1` `result` JSON envelope.
    4. Auto-indexing: inherited from shared status_set engine (for specs, no manifest exists so cleanly no-ops).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted `tests/test_set_dispatch_parity.py` run under both the local timezone and `TZ=UTC` with every specs agreement assertion passing UNCHANGED; the flipped expected-difference assertions named individually with their old and new values; and pasted results for the new `tests/test_specs_set_adapter.py`.
  - Observed evidence:
    `tests/test_set_dispatch_parity.py` under local timezone:
    25 passed in 2.85s
    `tests/test_set_dispatch_parity.py` under TZ=UTC:
    25 passed in 2.95s

    Flipped expected-difference assertion in tests/test_set_dispatch_parity.py:
    - test_specs_selector_resolution_expected_difference:
      Old:
        self.assertEqual(rc_status, 2, "Expected path-only specs set to refuse non-path selector")
        self.assertIn("cannot read sp0001", err_status)
      New:
        self.assertEqual(rc_status, 0)
        self.assertTrue(list(self.repo.glob(".aw/records/specs/to-review/*sp0001*")))

    New module tests/test_specs_set_adapter.py:
    `python3 -m pytest tests/test_specs_set_adapter.py -o addopts=""`
    ============================== 6 passed in 0.49s ===============================
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: the `CHANGELOG.md` hunk diffed; a grep over it for em and en dashes returning nothing; confirmation that it names the three user-visible changes plus each E-07 `changed` row, does NOT describe the delegation, and makes no clock claim.
  - Observed evidence:
    CHANGELOG.md hunk diff:
    ```diff
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th
     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Changed: `aw specs set --status` now accepts the same selectors as the positional spelling (an id6 or a setid, in addition to a file path), requires `--yes` for machine-readable callers (`--agent` or `--json`), and validates post-transition spec conformance before writing, refusing non-conforming results with a nonzero exit code while preserving the file byte-identical. In addition, descriptive flag violations (`--message`, `--blocks-release`, `--from-backlog`, `--gate-summary`) and malformed `--graduated-to` values on this spelling now exit 2 with the `aw set:` message prefix.
     - Added: an executing agent can now propose a gate, tool, or approach change in its outcome JSON under the proposal field. The runner validates the proposal and files it as a single tracked record on main via a coordinator worktree (a draft plan in its own Set for small proposals, or an open backlog item for material proposals) independent of whether the lane merges. The proposing item stops with fail-gate disposition awaiting a human decision, dependents cascade to dependency-blocked, independent items continue, and the proposal is surfaced at the top of the run summary.
    ```
    Grep over diff for em and en dashes:
    has_em: False, has_en: False (verified clean via regex [\u2013\u2014]).
    Names 3 user-visible changes: selector widening (id6/setid), confirmation gate (--yes), post-transition conformance validation.
    Names changed refusal rows: --message, --blocks-release, --from-backlog, --gate-summary, and --graduated-to exit 2 with aw set: prefix.
    Does not describe delegation implementation; makes no clock claim.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the pasted per-shape reachability table (each direct-caller module's `Namespace` shape, resolved yes or no, and the fix chosen); the pasted refusal table with rc and message on both spellings before, and after delegation, every row marked `preserved` or `changed`; a pasted history line read back after delegation showing `(aw specs)` (and `(aw specs, --by-human)` for an attested approval); and for each `changed` row the test path edited.
  - Observed evidence:
    Per-shape reachability table:
    | Module | Namespace Shape | Resolved | Fix Chosen |
    |---|---|---|---|
    | `test_specs_verbs.py` | `Namespace(path=..., status="to-review", message="msg", force=False)` (bare path outside repo) | Yes | Passed `repo_root=specs._repo_root_of(path)` from adapter; `_repo_root_of` falls back to `path.parent` when not in git repo |
    | `test_specs_status_dirs.py` | `Namespace(path=..., status="reviewed", message=None, force=False, by_human=False, evidence=None)` | Yes | Preserved default None values, resolved via repo root |
    | `test_specs_from_backlog.py` | `Namespace(path=..., status="to-review", from_backlog="bk0001", message="link", force=False)` | Yes | Carried `--from-backlog` preflight into shared engine |
    | `test_spec_review_attestation.py` | `Namespace(path=..., status="approved", by_human=True, message="LGTM", force=False)` | Yes | Passed `by_human` through to shared engine |
    | `test_stdin_interactive.py` | `Namespace(path=..., status="approved", message="LGTM", by_human=False)` | Yes | Preserved interactive approval prompt / refusal logic |
    | `test_specs_date_containment.py` | `Namespace(path=..., status="to-review", date="2020-01-01", message="dated")` | Yes | Type-scoped `--date` override pass-through in `status_set.py` |

    Refusal table:
    | Refusal condition | Before: --status spelling | Before: positional spelling | After delegation | Status | Test path edited |
    |---|---|---|---|---|---|
    | Unknown status | rc 1, `aw specs set: '<status>' is not a spec status ...` | rc 2, `aw set: '<status>' is not a valid status for specs` | rc 2, `aw set: '<status>' is not a valid status for specs` | changed | n/a (not pinned) |
    | Missing `- Status:` bullet | rc 1, `aw specs set: spec has no '- Status:' bullet` | rc 1, `refused: ... has no - Status: bullet` | rc 1, `aw specs set: refused: ... has no - Status: bullet` | preserved | n/a |
    | Illegal transition | rc 1, `aw specs set: illegal transition <old> -> <new>` | rc 1, `refused: illegal transition <old> -> <new>` | rc 1, `aw specs set: refused: illegal transition <old> -> <new>` | preserved | n/a |
    | Human-only approval (`->approved` without `--by-human`) | rc 1, `aw specs set: ... requires interactive human confirmation` | rc 1, `refused: approval requires interactive confirmation or attested flag` | rc 1, `aw specs set: refused: approval requires interactive confirmation or attested flag` | preserved | n/a |
    | Missing/unresolvable evidence (`->implemented`) | rc 1, `aw specs set: ... requires a resolvable --evidence citation` | rc 1, `refused: ... requires a resolvable --evidence citation` | rc 1, `aw specs set: refused: ... requires a resolvable --evidence citation` | preserved | n/a |
    | `->reviewed` without review record | rc 1, `aw specs set: ... requires a review record` | rc 1, `refused: ... requires a review record` | rc 1, `aw specs set: refused: ... requires a review record` | preserved | n/a |
    | Deferred gate pair missing/invalid | rc 1, `aw specs set: deferred requires a valid --gate-kind and --gate-ref` | rc 1, `aw specs set: deferred requires a valid --gate-kind and --gate-ref` | rc 1, `aw specs set: deferred requires a valid --gate-kind and --gate-ref` | preserved | n/a |
    | Unsafe `--gate-summary` | rc 1, `aw specs set: --gate-summary must be a bounded single control-char-free line` | rc 2, `aw set: --gate-summary must not contain embedded newlines` | rc 2, `aw set: --gate-summary must not contain embedded newlines` | changed | `tests/test_specs_releases_descriptive_safety.py`, `tests/test_specs_set_gate_parity.py` |
    | Unsafe `--message` | rc 1, `aw specs set: --message must not contain embedded newlines` | rc 2, `aw set: --message must not contain embedded newlines` | rc 2, `aw set: --message must not contain embedded newlines` | changed | `tests/test_specs_releases_descriptive_safety.py` |
    | Unsafe `--blocks-release` | rc 1, `aw specs set: --blocks-release must not contain embedded newlines` | rc 2, `aw set: --blocks-release must not contain embedded newlines` | rc 2, `aw set: --blocks-release must not contain embedded newlines` | changed | `tests/test_specs_releases_descriptive_safety.py` |
    | Unsafe `--from-backlog` | rc 1, `aw specs set: --from-backlog must not contain embedded newlines` | rc 2, `aw set: --from-backlog must not contain embedded newlines` | rc 2, `aw set: --from-backlog must not contain embedded newlines` | changed | `tests/test_specs_releases_descriptive_safety.py` |
    | Malformed `--graduated-to` | rc 2, `aw specs set: --graduated-to takes lowercase-kebab setids` | rc 2, `aw set: --graduated-to takes lowercase-kebab setids` | rc 2, `aw set: --graduated-to takes lowercase-kebab setids` | changed (prefix) | `tests/test_specs_releases_descriptive_safety.py` |
    | Unresolvable `--from-backlog` | rc 2, `aw specs set: unresolvable backlog id ...` | rc 2, `aw set: unresolvable backlog id ...` | rc 2, `aw set: unresolvable backlog id ...` | changed (prefix) | n/a |
    | Post-write `validate_spec` conformance | rc 1, `aw specs set: the resulting spec would not conform; refused` | (did not validate) | rc 1, `aw specs set: the resulting spec would not conform; refused` | preserved | n/a |

    History lines read back after delegation:
    Standard transition:
    - 2026-10-09 to-review (aw specs): status set to to-review
    Attested approval transition (--by-human):
    - 2026-10-09 approved (aw specs, --by-human): LGTM
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any
execution. IT IS ADDITIONALLY GATED ON SPEC `wy9aru` OQ-1, a BLOCKING open question owned by the
maintainer: E-03 implements whichever answer arrives and must not guess. That gate is MECHANICAL, not
a note: this plan carries `- Item-Dependencies: state:spec:approved:wy9aru`, so the runner's dependency
check makes it ineligible to dispatch until the spec reaches `approved`, which is the transition that
requires the maintainer to have answered. If execution nonetheless begins before the answer exists
(for example because the spec was approved with OQ-1 still open), perform E-01, E-02 and every
independent part, STOP at E-03, and report the block rather than choosing a branch.

It depends on child 03 (`m1jlwm`) having EXECUTED, so the two release-gated gate bypasses are fixed
across the existing fork before the fork is removed, and on child 02's harness existing, since that
harness is this plan's primary evidence. Plan `ulepef` must also have landed (F-02): it owns the
sidecar write ORDER that E-03 adopts.

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths` plus any widening declared at execution time, through `aw commit <plan> -- <paths>`;
never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste ACTUAL runner output for
every test claim. Verify the staged set with `git diff --cached --name-only` before committing, and
re-verify after any failed commit attempt, because a rejecting hook can leave paths in the index that
you never staged. Per `wy9aru` S5, the spec amendment lands in the same commit as the behavior it
describes.

Scope fence: the declared `Scope-Paths` plus the conditional test paths named in "Scope check" are a
DECLARATION, not a stop condition; an out-of-scope edit is made and then justified with a
`--scope-reason`, and a declared path left untouched (for example the `1525-02` spec under a branch that
does not need it) takes a `--scope-ack`. The one STOP in this plan is E-03's, for an unanswered
maintainer decision.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Under `aw oc run` / `aw agy run` the runner performs that transition;
when executed by hand, the executor runs `aw ipd finalize` for it. Never hand-`git mv` the file. Do not set the backlog item `fcnz1r` to any status: the orchestrator
`63zo2f` owns its disposition.
