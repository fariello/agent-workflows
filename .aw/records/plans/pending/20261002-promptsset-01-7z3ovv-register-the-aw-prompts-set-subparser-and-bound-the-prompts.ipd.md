# IPD: Register the aw prompts set subparser and bound the prompts status vocabulary to its five buckets

- Date: 2026-10-02
- Kind: child
- Concern: `cli.main` carries a live dispatch arm routing `prompt_cmd == "set"` to `status_set.run_set_command(..., scoped_type="prompts")`, and the `prompts` family description advertises that `'set' transitions a staged prompt's status`, but `prompts_sub` registers only `new`, so `aw prompts set <status> <sel>` dies in argparse with `invalid choice: 'set' (choose from 'new')` and the arm is unreachable. The surface is simultaneously DECLARED: `command_surface.COMMAND_INVENTORY` carries a full `CommandDeclaration(command="prompts set", ...)`, so `get_declared_leaves()` reports it as one of 162 declared leaves while `conformance_matrix.build_matrix` reports it in `declared_absent` and SKIPS every coverage row for it. Registering the subparser is not a one-line fix, because the shared setter's prompts vocabulary is WRONG in a way the untyped spelling already exposes: `status_set.TYPE_STATUSES["prompts"]` is a verbatim copy of the plans vocabulary (11 tokens including `draft`, `to-review`, `reviewed`, `approved`, `auto-approved`), while the prompts tree has exactly FIVE buckets, so six of those eleven tokens resolve to the `pending` bucket and write a `- Status:` the tree has no directory for.
- Scope: IN: (1) register a `set` subparser on the `prompts` family so the shipped dispatch arm and the shipped `CommandDeclaration` both become reachable, with the flag surface the declaration already names; (2) narrow `status_set.TYPE_STATUSES["prompts"]` from the copied plans vocabulary to the five real buckets DERIVED from `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]` (never re-listed), keeping `done` as the existing `executed` alias that `normalize_target_status` already implements; (3) make the setter write a prompt's status into its single leading `<!-- aw-prompt: ... -->` metadata comment instead of prepending a `- Status:` bullet, because the bullet is a measured corruption of a pasteable prompt and a measured `aw check prompts` error. OUT: the plan does NOT register any other missing prompts verb (`aw prompts check` is retired by maintainer decision, see Deferred), does NOT touch the untyped `aw set`'s own grammar, does NOT change which prompts a selector MATCHES, does NOT touch any other tree's vocabulary, and does NOT alter the five bucket names or the `attention_contract` class mapping.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/status_set.py, agent_workflows/prompts.py, agent_workflows/command_surface.py, tests/test_status_set.py, tests/test_exit_contract_conformance.py, tests/test_prompts_set_surface.py, tests/test_status_set_descriptive_safety.py, docs/artifact-lifecycles.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: um8ikz
- Blocks-Release: next
- Set: promptsset
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7z3ovv

## Workflow history
- 2026-10-02 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Re-verified at lane HEAD 83888bf53 (F-01..F-04, F-11 reproduce). Fixed: 68sur3 already graduated to gm9baj so E-07 no longer edits it and coordinates with gm9baj's allow-set (PR-001); in-process narrowing measured 4 failed existing prompt tests, now re-targeted in E-06 with tests/test_status_set_descriptive_safety.py added to scope (PR-002); live-count bars replaced by re-derived baseline and per-leaf scenario rows (PR-003); shared commit flags on the new leaf (PR-004); path-scoped negative-control stash (PR-005); scope fence + conditional finalize (PR-006); OQ owners (PR-007).

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `um8ikz`, graduating it. Every claim in Findings was MEASURED in this lane at HEAD `ccd7ee3b8`, by driving the real CLI and by calling the real functions, not read off the source. THE ITEM'S DIAGNOSIS IS CORRECT and its framing of the blocker is correct in KIND but understated in SEVERITY, and three facts were found that the item does not state and that change the shape of the fix. FIRST, the item frames the vocabulary question as needing a maintainer DECISION ("simply registering the subparser would expose a vocabulary question rather than settle it"). It does not: the repository already answers it mechanically, because `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]` and `attention_contract._PROMPTS_MAP` independently agree on the SAME five tokens, and the `specs` and `backlog` entries of the very same `TYPE_STATUSES` table are already DERIVED from their lifecycle dirs with in-code comments saying never to re-list them. The prompts entry is the outlier that was copy-pasted from plans. So the fix is to apply an established pattern, not to invent a vocabulary. SECOND, and this is the finding that matters most: the setter does not merely accept a wrong status, it CORRUPTS THE PROMPT. Measured end to end, `aw set executed <prompt-id6>` prepends a literal `- Status: executed` bullet, which for a prompt is visible text above the prompt body, breaking the select-all-and-paste property the whole tree exists for; on a prompt with a body it lands INSIDE the body, between the H1 and the first paragraph. The same write leaves the metadata comment's own `Status:` field untouched, so the two disagree, which `aw check prompts` then reports as `check.prompt-status-mismatch`. The item does not mention the metadata comment at all. THIRD, this is also a MISSING-COVERAGE defect and not only a dead-code defect: `conformance_matrix.build_matrix` reports `declared_absent: ['prompts set', 'upgrade-test']` and every required scenario row for the leaf is silently dropped, while `test_exit_contract_conformance.test_help_floor_gate` names `prompts set` in its own docstring as the one of thirteen `--help` divergences that is NOT an argparse.REMAINDER forwarder, a note that only makes sense because the leaf is dead. So the registration restores real conformance coverage rather than just removing an eyesore. The two measured writer defects are closed HERE rather than filed, because they are only reachable through the surface this plan makes reachable, and shipping a newly-reachable verb that corrupts its own artifact would be worse than leaving it dead.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw prompts set` work, and make it write a CONFORMING prompt when it does.

The verb is already dispatched in `cli.main` and already declared in `command_surface.COMMAND_INVENTORY`;
only the parser registration is missing, so one `add_parser("set", ...)` call makes a shipped code path
and a shipped contract declaration reachable together. But the shared setter it reaches is wrong for
prompts in two measured ways, and both are only reachable through this surface, so both are closed in the
same change: it accepts six statuses the tree has no bucket for, and it writes the status as a `- Status:`
bullet that corrupts the prompt body and desynchronizes the metadata comment the tree's own checker reads.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: settle the vocabulary before anything becomes reachable

- [ ] E-01 Narrow `status_set.TYPE_STATUSES["prompts"]` from its current verbatim copy of the plans
  vocabulary to the five real buckets, DERIVED from `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]` rather
  than re-listed, plus the ONE alias `done` that `normalize_target_status` already maps to `executed` for
  `record_type in ("plans", "prompts")`.
  FOLLOW THE TWO ESTABLISHED PRECEDENTS IN THE SAME TABLE, do not invent a shape: the `specs` entry is
  already `set(_LD.LIFECYCLE_SUBDIRS["specs"])` and the `backlog` entry is already
  `set(_backlog_mod.STATUSES)`, each carrying an in-code comment stating it is derived and "never
  re-listed". The backlog comment additionally records WHY (a re-listed copy "is what refused `aw backlog
  set graduated` after the vocabulary grew"), which is the identical failure mode this item is an instance
  of, with the polarity reversed: here the stale copy ACCEPTS six tokens the tree retired rather than
  refusing one it gained.
  KEEP THE `pending` ALIAS WORKING AND DO NOT ADD IT TO THE DERIVED SET. `normalize_target_status` maps
  `pending -> to-review` for prompts today, and `to-review` is NOT a prompt bucket, so that alias must be
  re-pointed or removed rather than carried: decide it in OQ-01 and implement the decision here. The
  validation for this item must drive the token either way, so whichever OQ-01 resolves to is pinned.
  RECORD THE BASELINE FIRST: before any edit, run the bare suite (`python3 -m pytest`) once and record
  its summary line and failed-node set as `<baseline>`; later gates compare against it, not against
  "zero failures", because unrelated load-sensitive nodes (backlog `wc5c5e`) may fail at HEAD.
  NARROWING BREAKS FOUR EXISTING TESTS, MEASURED AT REVIEW, and they must be re-pointed in E-06 rather
  than the narrowing being weakened. Applying exactly this narrowing in-process and running
  `tests/test_status_set.py tests/test_status_set_descriptive_safety.py` gave `4 failed, 104 passed`:
  `test_status_set.py::TestStatusSetCommands::test_prompt_set` (sets a prompt `approved`),
  `::TestStatusSetCommands::test_set_multiple_mixed_types` (sets a plan, spec AND prompt `reviewed` in one
  call; refused `Status 'reviewed' is not valid for prompts (valid: ['done', 'executed', 'not-executed',
  'pending', 'reusable', 'superseded'])`), `::TerminalReopenRefusalTests::test_a_non_plan_artifact_transition_is_unaffected`
  (sets a prompt `draft`), and `test_status_set_descriptive_safety.py::TestLengthAsymmetryAndNonRegressions::test_conforming_transitions_across_five_trees`
  (sets a prompt `to-review`). Each pins the DEFECT this item fixes (a non-bucket status accepted for a
  prompt), so the refusal is the intended behavior change and not a regression.
  - Depends on: none
  - Expected outcome: `sorted(status_set.TYPE_STATUSES["prompts"])` is the five bucket names plus the
    retained alias(es) and nothing else; `aw set prompts draft <id6>` REFUSES with the existing
    `Status 'draft' is not valid for prompts (valid: [...])` message naming only the narrowed set; and
    `aw set prompts executed <id6>` still succeeds.
  - Execution state: pending

- [ ] E-02 Make the shared setter write a PROMPT's status into its single leading
  `<!-- aw-prompt: ... -->` metadata comment, not as a `- Status:` bullet.
  THIS IS THE CORRUPTION HALF AND IT IS NOT COSMETIC. `status_set.apply_status_change`'s front-matter
  writer has two shapes (a fenced YAML `status:` scalar and a `- Status:` bullet) and a prompt has
  NEITHER, so the `if not status_updated:` fallback inserts a bullet. Measured on a real minted prompt,
  the bullet lands as the file's FIRST line above the metadata comment when the file has no `# ` heading,
  and lands BETWEEN the H1 and the first body paragraph when it has one. Either is visible text in a file
  whose entire contract is that selecting all and pasting yields a clean prompt
  (`.aw/records/prompts/README.md`: the id6 is "never a `- Id:` bullet, which would render as visible text
  above the prompt body"). Plan `ubac5n` E-04 already established that a prompt's identity is written
  through the metadata comment for exactly this reason, and plan `3b01h9`'s review recorded the READER
  half of the same asymmetry.
  REUSE THE SHIPPED WRITER FAMILY, DO NOT ADD A THIRD IN-FILE FORMAT. `prompts.inject_metadata_id6` is the
  existing precedent for writing a key INTO that one comment (idempotent, returns the text unchanged when
  there is no comment, deliberately never mints one); `prompts.render_metadata_comment` is the renderer;
  `prompts_index._parse_metadata_comment` is the reader `check_engine.validate_prompt_content` already
  uses. A status writer belongs in `prompts.py` beside them, consumed by `status_set` under a
  `record_type == "prompts"` branch, not reimplemented inline.
  HANDLE THE SIX COMMENTLESS PROMPTS HONESTLY. Measured: 17 of 17 tracked prompts carry the comment today,
  but `prompts.has_metadata_comment`'s own docstring records 11-of-17 at the 2026-09-20 measurement and
  `inject_metadata_id6` deliberately returns such a file UNCHANGED rather than minting a comment, because
  minting one would add a line above the body it exists to protect. The status writer MUST adopt the same
  refusal-to-mint posture and the transition must still RELOCATE the file (the directory is the real
  lifecycle), reporting plainly rather than silently repairing.
  - Depends on: E-01
  - Expected outcome: after `aw set prompts executed <id6>` on a prompt with a body, the file's first line
    is still its metadata comment with `Status: executed` inside it, the body is byte-identical, no
    `- Status:` bullet exists anywhere in the file, and `aw check prompts` reports zero findings.
  - Execution state: pending

### Task group 2: make the declared surface reachable

- [ ] E-03 Register a `set` subparser under `prompts_sub` in `cli._build_parser`, so the shipped
  `prompt_cmd == "set"` dispatch arm in `cli.main` is reachable and the shipped
  `CommandDeclaration(command="prompts set", ...)` stops being `declared_absent`.
  DERIVE THE FLAG SURFACE FROM THE DECLARATION THAT ALREADY SHIPS, not from preference: it names
  `legacy_flags=("--message", "--by-human", "--dry-run", "--json", "--agent")` and
  `exit_contract=(0, 1, 2)`. `--json`/`--agent` arrive via the shared `common` parent every other leaf
  uses. The positional is `args` with `nargs="+"` taking `<status> <selector...>`, matching `p_ipd_set`,
  which is the closest shipped sibling reaching the same engine with a `scoped_type`.
  ALSO REGISTER THE SHARED COMMIT FLAGS with `cli._add_commit_flags(p_prompts_set)`, as `p_ipd_set`
  does: `status_set._offer_self_commit` reads `args.commit`/`args.no_commit`, and without them a TTY run
  can only commit by prompt and a non-interactive run can never commit (`_add_commit_flags` docstring).
  Add `--commit`/`--no-commit` to the declaration's `legacy_flags` alongside `--dir`/`--yes`.
  ALSO ADD `--dir` AND `--yes`, AND SAY WHY IN THE PLAN: every other surface reaching
  `run_set_command` declares `--dir` (the engine resolves a repo root from it) and `--yes` (the
  confirmation gate reads it), and a leaf that honors a flag it does not declare is the `SHOULD` C5 of
  spec `wy9aru` warns about in reverse. These are additions to the declaration, so update
  `command_surface.py`'s `legacy_flags` in the same edit rather than leaving the declaration stale.
  DO NOT COPY `p_ipd_set` WHOLESALE. It carries eleven plan-specific flags (`--from-spec`,
  `--allow-open-questions`, `--allow-terminal-reopen`, `--actor`, `--scope-reason`, `--scope-ack`,
  `--graduated-to`, `--priority`, `--work-kind`, `--blocks-release`, `--from-backlog`) that are
  meaningless on a prompt, which carries no gate fields, no release gate and no approval field. Spec
  `wy9aru`'s own honest-limits section names putting a meaningless flag on a verb as the reason its
  flag-convergence criterion is a `SHOULD` and not a `MUST`.
  - Depends on: E-02
  - Expected outcome: `aw prompts set --help` exits 0 and lists the declared flags;
    `aw prompts set executed <id6> --dry-run` previews and writes nothing;
    `conformance_matrix.build_matrix(cli._build_parser()).declared_absent` no longer contains
    `prompts set`.
  - Execution state: pending

- [ ] E-04 Correct the two shipped prose claims that describe this surface, now that it exists.
  `cli._COMMAND_DESCRIPTIONS["prompts"]` already says `'set' transitions a staged prompt's status` and was
  a falsehood for as long as the parser rejected it; it becomes TRUE here and needs no edit, so state that
  explicitly rather than touching it. What DOES need editing is the `p_prompts` `add_parser` call, whose
  `help`, `description` and `epilog` all describe a one-verb family (`"'new' mints a conforming staged
  prompt"`, three `aw prompts new` examples, `Exit codes: 0 clean, 2 cannot-run/usage error` which omits
  the declared `1`).
  ALSO CORRECT `docs/artifact-lifecycles.md`, which twice publishes the untyped spelling as THE way to
  change a prompt's status (`Change a tracked prompt's status with` the untyped form, and the quick-
  reference row `| Prompt | ... | aw set prompts <status> <sel> | ...`). Both become one of two valid
  spellings. The quick-reference row for every OTHER type already names that type's own typed verb
  (`aw ipd set`, `aw spec set`, `aw backlog set`), so the prompts row was the outlier only because the
  typed verb did not work.
  THE SAME DOC SECTION'S BUCKET TABLE AND MERMAID DIAGRAM ARE CORRECT AND MUST NOT BE TOUCHED: both
  already list exactly the five buckets this plan narrows the vocabulary to, which is independent
  corroboration for E-01 and would be destroyed by "harmonizing" them with the old eleven-token set.
  - Depends on: E-03
  - Expected outcome: the family help describes two verbs and the full three-value exit contract; the two
    `docs/artifact-lifecycles.md` sites name both spellings; the bucket table and diagram are
    byte-unchanged.
  - Execution state: pending

### Task group 3: prove it, and prove the old defects are gone

- [ ] E-05 Add `tests/test_prompts_set_surface.py` driving the NEW leaf through the CLI, with the
  registration, the vocabulary and the comment-write each pinned by a test that FAILS on today's code.
  DRIVE `cli.main`, NOT `run_set_command`, for the registration cases. The defect is an argparse
  rejection, so a test calling the engine directly cannot see it: that is precisely why 17 broken prompt
  rows and one dead leaf shipped green. `tests/test_status_set.py` already builds a prompts fixture
  (`StatusSetTestBase.create_prompt`), but note its fixture writes a `- Status:` BULLET and no metadata
  comment, which is the shape E-02 makes non-canonical, so this module needs its own fixture minted the
  way `aw prompts new` mints one (metadata comment, no bullet, no body) plus a variant WITH a body.
  PIN THE REFUSAL MESSAGE, NOT ONLY THE EXIT CODE, for the vocabulary case. The shipped refusal already
  enumerates the valid set in its text (`Status 'staged' is not valid for prompts (valid: ['approved',
  'auto-approved', ...])`), so asserting the enumerated set is what proves E-01 narrowed it rather than
  merely that something refused.
  ASSERT BODY BYTE-IDENTITY FOR THE COMMENT-WRITE CASE, and RE-RESOLVE THE PATH AFTER EVERY ACCEPTED
  CALL, because an accepted transition MOVES the file between buckets. Plan `4gwgo3` E-04 records losing
  a review cycle to a `FileNotFoundError` from exactly this, and names not sharing a cached-path helper
  between the refused and accepted cases as the fix.
  - Depends on: E-04
  - Expected outcome: a new module whose cases fail on pre-change code (the registration case with
    `SystemExit(2)` / `invalid choice: 'set'`, the vocabulary case by ACCEPTING `draft`, the writer case
    by finding a `- Status:` bullet) and pass after.
  - Execution state: pending

- [ ] E-06 Re-point the existing tests whose recorded premise this plan falsifies: the two that assert
  the verb is dead, and the four (E-01) that drive a prompt to a status the narrowed vocabulary refuses.
  FOR THE FOUR VOCABULARY TESTS, change only the PROMPT member's target to a real bucket while keeping
  each test's assertion about what it actually pins: `test_prompt_set` -> a bucket such as `executed`
  (and assert the status lands in the metadata comment or, for the commentless bullet fixture, per the
  OQ-02 posture E-02 implements); `test_set_multiple_mixed_types` -> keep the plan and spec at `reviewed`
  and drop or re-target the prompt member, since one token cannot be valid for all three trees now, and
  ADD the refusal as an explicit assertion that a mixed batch carrying a prompt at `reviewed` is refused
  BEFORE making changes (the measured `Refusing before making changes.`); `test_a_non_plan_artifact_transition_is_unaffected`
  -> move the prompt `executed -> pending` instead of `-> draft`, which still proves the plan terminal
  guard does not leak onto prompts; `test_conforming_transitions_across_five_trees` -> a real bucket in
  place of `to-review`. Do NOT widen the vocabulary to keep any of them green.
  `tests/test_status_set.py::test_a_non_plan_artifact_transition_is_unaffected` carries the docstring
  "Driven through the UNTYPED `aw set other` spelling because `aw prompts set` is not a live parser
  surface (`aw prompts` accepts only `new`)". Its ASSERTION is about the plan terminal guard not leaking
  onto prompts and stays valid and valuable; only the stated REASON for the spelling expires. Correct the
  docstring and ADD the typed spelling as a second case rather than replacing the untyped one, since both
  spellings must keep working (spec `wy9aru` 3a: "Both spellings keep working").
  `tests/test_exit_contract_conformance.py::test_help_floor_gate`'s docstring names `prompts set` among
  thirteen leaves that exit 2 from an in-process `--help` and calls it "the exception, exiting 2 in
  subprocess too". After E-03 it exits 0 like the other 149, so the count and the named exception both
  change. DO NOT weaken the gate to accommodate it: it SKIPS any leaf whose observed code is non-zero and
  derives the observation dynamically, so a now-conforming leaf simply stops being skipped. Update the
  docstring's census to what you MEASURE after the change and paste that measurement, rather than
  decrementing the number by hand.
  THE FIXTURE IN `test_status_set.py` ALSO NEEDS A DECISION RECORDED: `create_prompt` writes a bullet-
  shaped prompt that no shipped minting path produces. Leave it as-is (it exercises the legacy/hand-
  written shape, which E-02 must still handle without crashing) and say so in the plan, so a later reader
  does not "fix" the fixture and silently delete that coverage.
  - Depends on: E-05
  - Expected outcome: both docstrings state what is now true with a pasted measurement; the plan-guard
    assertion still holds and now runs on both spellings; the four vocabulary tests target real buckets
    and `test_set_multiple_mixed_types` additionally asserts the refusal; no gate is weakened.
  - Execution state: pending

- [ ] E-07 Confirm the duplicate backlog item `68sur3` is ALREADY carried, and run the whole-repository
  validation gate.
  `68sur3` FILES THE SAME DEFECT AS `um8ikz` (F-12). RE-MEASURED AT REVIEW (HEAD `83888bf53`): it is NO
  LONGER `open`. It sits in `.aw/records/backlog/graduated/` with history `2026-10-02 graduated (aw
  backlog): graduated by run run-20261001T221821Z-1985969: gm9baj`, `- Graduated-To: declabsent`, and an
  unchanged `- Blocks-Release: next`; its carrier is pending plan `gm9baj` (`- From-Backlog: 68sur3`),
  which restores the declared-but-absent leaf gate and deliberately leaves the registration to THIS plan.
  So there is NOTHING to graduate here, and this plan must NOT edit `68sur3` at all (no
  `aw backlog set`, no added `From-Backlog`, no gate change): re-graduating it would be a no-op at best,
  and pointing it at `7z3ovv` would sever `gm9baj`'s HANDOFF carrier. `aw backlog set done 68sur3` would
  FAIL CLOSED (`check_engine.evaluate_blocking_close`) while `gm9baj` is unexecuted, and
  `--blocks-release -` would silently drop a real release gate; neither is this plan's act.
  COORDINATE WITH `gm9baj` ON ONE POINT. `gm9baj` E-02 seeds an allow-set of declared-but-unreachable
  commands with EXACTLY `prompts set` and asserts SET EQUALITY, and its failure message tells "whichever
  plan executes second" to delete the stale entry. If `gm9baj` has ALREADY executed when this plan runs,
  E-03 makes that entry stale and the gate goes red in this plan's full-suite run: DELETE the
  `prompts set` entry from that allow-set (it lives in `tests/conformance_matrix.py` and/or
  `tests/test_command_surface_declarations.py` per `gm9baj`), justify the out-of-declared-scope path at
  finalize with `--scope-reason`, and report it. If `gm9baj` has NOT executed, do nothing; its own
  executor removes the entry.
  THEN RUN THE REPOSITORY-WIDE GATE, which is this plan's last action and not a formality: the bare full
  suite, `aw check all`, and a staged-path inspection. Run the suite BARE (`python3 -m pytest`): `addopts`
  already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so adding `-n0` makes
  it several times slower and adding `-q` suppresses the very summary line the execution contract requires
  you to paste.
  - Depends on: E-06
  - Expected outcome: `68sur3` is byte-unchanged by this plan (still `graduated` to `gm9baj`, still
    `- Blocks-Release: next`); the bare suite reports no failure absent from the pre-edit baseline recorded
    in E-01; `aw check all` reports no new findings.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `status_set.TYPE_STATUSES` is a per-type status vocabulary table in which TWO of six entries are
  already DERIVED from a single source rather than listed (`"specs": set(_LD.LIFECYCLE_SUBDIRS["specs"])`,
  `"backlog": set(_backlog_mod.STATUSES)`), each with an in-code comment stating it must never be
  re-listed and the backlog one naming the exact bug a stale copy caused. The `"prompts"` entry is a
  verbatim duplicate of the `"plans"` entry, which is the only reason the plans vocabulary applies to
  prompts at all.
- `lifecycle_dirs.LIFECYCLE_SUBDIRS` is the one source of a type's lifecycle directories and is exposed
  through a `types.MappingProxyType`, i.e. read-only by construction. `record_placement.target_subdir`
  consumes it, and for `record_type in ("plans", "prompts")` routes any `_plans.PRE_TERMINAL` status to
  `pending`, which is the mechanism by which six non-bucket tokens currently resolve to a real directory
  and so write a status the tree cannot represent.
- A prompt's in-file metadata lives in ONE leading HTML comment, never a bullet and never YAML. This is
  stated in `.aw/records/prompts/README.md`, enforced for the id6 by `prompts.inject_metadata_id6` (which
  is idempotent and refuses to mint a comment that does not exist), and checked by
  `check_engine.validate_prompt_content` via `prompts_index._parse_metadata_comment`
  (`check.prompt-metadata-missing`, `check.prompt-id-mismatch`, `check.prompt-status-mismatch`). The
  original rationale was approved spec `20260808-1958-01-prompt-purity-lint` R1/P4; that spec is now
  `superseded` and its lint `aw prompts check` was DECLINED by the maintainer on 2026-09-26, so the
  convention is live and documented but has no mechanical gate beyond the three `check` rules above. Cite
  the README and the code, not the superseded spec, as plan `iyi4hc`'s review (PR-003) required.
- `command_surface.COMMAND_INVENTORY` is the normative declaration of every CLI leaf's output contract,
  and `tests/conformance_matrix.py` derives required coverage rows FROM it. A declaration whose command is
  absent from the parser is reported in `declared_absent` and generates ZERO coverage rows, so a dead leaf
  loses its conformance coverage silently.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended
  to one of those and never alone: an offset expires before this plan executes (spec
  `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Every row was measured in this lane at HEAD `ccd7ee3b8` on 2026-10-02, by driving the real CLI or calling
the real functions. Probe artifacts were created and removed; `git status --porcelain` is empty of them.

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE ITEM REPRODUCES EXACTLY.** The leaf is rejected by argparse while the dispatch arm behind it is live. | `aw prompts set executed foo` exits **2** with `agent-workflows prompts: error: argument prompts_command: invalid choice: 'set' (choose from 'new')`. `cli.main` contains `if prompt_cmd == "set": ... return status_set.run_set_command(args.args, scoped_type="prompts", args=args, term=term)`. `prompts_sub = p_prompts.add_subparsers(dest="prompts_command")` is followed by exactly one `add_parser("new", ...)`. |
| F-02 | **THE DEAD LEAF IS ALSO A DECLARED LEAF, so this is a missing-COVERAGE defect and not only dead code.** The item does not mention the declaration. | `command_surface.get_declaration("prompts set")` returns a full `CommandDeclaration(command_class='mutation', human_recipe='status', agent_record_kind='result', mutation_gate='auth_floor', legacy_flags=('--message', '--by-human', '--dry-run', '--json', '--agent'), exit_contract=(0, 1, 2), migrated=True, in_boundary=True)`. `'prompts set' in command_surface.get_declared_leaves()` is **True** (162 declared leaves). `conformance_matrix.build_matrix(cli._build_parser())` reports `undeclared: []` and `declared_absent: ['prompts set', 'upgrade-test']`, and its `declared_absent` branch `continue`s BEFORE emitting any `MatrixRow`, so all of the leaf's required scenarios are dropped from the 1193 rows. |
| F-03 | **THE VOCABULARY QUESTION THE ITEM CALLS A BLOCKER IS ALREADY ANSWERED BY THE REPOSITORY, TWICE, INDEPENDENTLY.** It needs no maintainer decision. | `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]` is `('pending', 'executed', 'superseded', 'not-executed', 'reusable')`. `sorted(attention_contract.CLASS_MAPS["prompts"])` is `['executed', 'not-executed', 'pending', 'reusable', 'superseded']` - the SAME five. `docs/artifact-lifecycles.md`'s prompts bucket table lists the same five and nothing else. All 17 tracked prompts carry one of exactly those five as their comment `Status:`. |
| F-04 | **`TYPE_STATUSES["prompts"]` IS A VERBATIM COPY OF THE PLANS VOCABULARY and admits ELEVEN tokens, six of which name no bucket.** | `sorted(status_set.TYPE_STATUSES['prompts'])` is `['approved', 'auto-approved', 'done', 'draft', 'executed', 'not-executed', 'pending', 'reusable', 'reviewed', 'superseded', 'to-review']`. Resolving each through `normalize_target_status` then `record_placement.target_subdir`: `approved`, `auto-approved`, `draft`, `reviewed`, `to-review` and `pending` ALL land in the `pending` bucket, i.e. six tokens collapse onto one directory while writing six different `- Status:` values. The `specs` and `backlog` entries of the same table are DERIVED from their lifecycle sources with comments saying never to re-list; prompts is the outlier. |
| F-05 | **THE SETTER CORRUPTS THE PROMPT, which is the severe finding and which the item does not mention at all.** A `- Status:` bullet is prepended as visible text into a file whose whole contract is select-all-and-paste purity. | Minted a real prompt with `aw prompts new --kind research --slug um8ikz-probe-scratch --set um8ikzprobe --apply` (file content: one metadata comment line, no body). After `aw set executed kdqc8p --message '...'` (exit **0**), the file in `executed/` reads, in order: `- Status: executed`, then the `<!-- aw-prompt: ... -->` comment, then `## Workflow history`. **The bullet is the FIRST LINE OF THE FILE, above the metadata comment.** Cause: `status_set.apply_status_change`'s writer recognizes only a fenced YAML `status:` scalar or a `- Status:` bullet, and its `if not status_updated:` fallback inserts a bullet before the first `# `/`- Date:` line or at index 0. |
| F-06 | **ON A PROMPT WITH A BODY THE BULLET LANDS INSIDE THE BODY**, between the H1 and the first paragraph, which is worse than F-05 because it is unambiguously inside the pasteable region. | Second probe, minted the same way, then `printf '# A real prompt body\n\nSome content.\n' >>` the file. After `aw set to-review mmmco9` (exit 0) the file reads: comment, `# A real prompt body`, `- Status: to-review`, blank, `Some content.`, `## Workflow history`. A subsequent `aw set executed mmmco9` UPDATED that in-body bullet to `executed` in place, so the corruption is sticky and self-perpetuating rather than a one-time accident. |
| F-07 | **THE WRITE DESYNCHRONIZES THE FILE FROM ITS OWN CHECKER and `aw check prompts` reports it**, so the defect is visible to shipped tooling the moment the surface is used. | On the F-06 probe after its transition to `executed`, `aw check prompts` reported `check.prompt-status-mismatch`: `comment Status 'pending' inside terminal bucket 'executed'` (1 warning). On the F-05 probe it reported `check.prompt-metadata-missing` as an **error**, because the prepended bullet displaced the comment from the first line and `validate_prompt_content`'s `first_line.startswith("<!--")` test then fails. So one accepted transition converts a conforming prompt into a checker error. Both findings cleared when the probes were deleted (`errors 0 warnings 0`). |
| F-08 | **THE SETTER CANNOT READ A PROMPT'S OWN IDENTITY OR STATUS**, so every prompt enters the engine as a statusless record defaulting to `draft`. | `status_set.read_artifact_record(<the plainlang prompt>, Path('.'))` returns `record_type='prompts'` but `id6=None`, `status=None`, `set_id=None`, because `_ID_RE`/`_STATUS_RE`/`_SET_RE` match bullets and the prompt declares all three inside its comment (`_parse_metadata_comment` returns all of `Kind`, `Id`, `Set`, `Status`, `Created`, `Author`, `Targets`, `Concerns`). Over the whole tree, `inventory_all_artifacts(scoped_type='prompts')` returns 17 records of which **16 have `status=None`** (the one exception is a legacy file that happens to carry a literal `- Status: superseded` bullet in its retired body). `apply_status_change` then computes `old_status = (rec.status or "draft")`, so every prompt transition is reported as starting from `draft` - visible in the measured output `20261002-um8ikzprobe-01-kdqc8p  draft -> executed` for a prompt whose comment said `pending`. |
| F-09 | **SELECTOR RESOLUTION STILL WORKS DESPITE F-08**, so the fix is confined to the status read/write and does not need to touch matching. This bounds the blast radius. | `match_selector('ng0ga4', inventory_all_artifacts(scoped_type='prompts'), Path('.'), scoped_type='prompts')` returns exactly one record, the right file, even though its `id6` field is `None`: the filename slot carries the id6. This is consistent with plan `3b01h9`, which fixed the id6 DISPLAY and `--id`/`--set` FILTERS in `aw find` and explicitly "changes nothing about which records MATCH a selector". |
| F-10 | THE SHIPPED FAMILY HELP ALREADY PROMISES THE VERB, so the current state is a user-facing falsehood and not merely an omission. | `cli._COMMAND_DESCRIPTIONS["prompts"]` reads `"... 'new' mints a conforming staged prompt into pending/, and 'set' transitions a staged prompt's status. The prompt's lifecycle is its directory, so a transition moves the file."` Meanwhile `aw prompts --help` renders `{new}` and its own description/epilog describe only `new`, and its `OUTPUT & EXITS` block claims `Exit codes: 0 clean, 2 cannot-run/usage error`, omitting the `1` the shipped `prompts set` declaration carries. |
| F-11 | TWO EXISTING TESTS RECORD THE DEAD SURFACE AS A PREMISE, and both need re-pointing rather than deleting. | `tests/test_status_set.py::test_a_non_plan_artifact_transition_is_unaffected` docstring: "Driven through the UNTYPED `aw set other` spelling because `aw prompts set` is not a live parser surface (`aw prompts` accepts only `new`)". `tests/test_exit_contract_conformance.py::test_help_floor_gate` docstring names `prompts set` in its 13-leaf list and says "In a real subprocess, 12 of the 13 actually exit 0 ('prompts set' is the exception, exiting 2 in subprocess too)" - true only because the leaf is dead, since it is the one entry in that list that is not an `argparse.REMAINDER` forwarder. Measured: `aw prompts set executed foo` exits 2 in a real subprocess, agreeing with that docstring today. |
| F-12 | A SECOND BACKLOG ITEM FILES THE SAME DEFECT INDEPENDENTLY, and its analysis adds one consequence this plan should record. (REVIEW UPDATE: since authoring, `68sur3` was graduated to plan `gm9baj` and moved to `.aw/records/backlog/graduated/`; see E-07.) | `.aw/records/backlog/open/20261001-setdispgate-01-68sur3-prompts-set-dispatched-but-unregistered.backlog.md` (`open`, `Blocks-Release: next`, `Work-Kind: bug`) was filed 2026-10-01 while mapping the `set` dispatch surface for `fcnz1r`. It adds that `status_set._offer_self_commit`'s docstring enumerates `prompts set` among the surfaces one integration covers, "which an author reasonably reads as five live callers when four are live". Spec `wy9aru` E-3 and pending plan `63zo2f` both name `68sur3` as the carrier for this work; pending plan `5poaqh` independently measured the same dead surface in its own conventions section. See Deferred for the duplicate-resolution obligation. |
| F-13 | THE BASELINE IS GREEN ON EVERY MODULE THIS PLAN TOUCHES, so a failure after the change is this plan's. | `python3 -m pytest tests/test_command_surface_declarations.py tests/test_exit_contract_conformance.py tests/test_status_set.py tests/test_agent_surface_conformance.py` reported `139 passed in 13.54s` (1 deselected by the configured marker filter). `aw check prompts` on the clean tree reported `checked 2, errors 0, warnings 0, info 1` (the `info` is the standing "cross-tree collisions NOT checked by a per-type run" notice). |
| F-14 | **A PROBE REVEALED THAT `aw set` SELF-COMMITS, which an executor must know before driving this surface by hand.** | `aw set prompts pending vocab-probe --yes` (on a TTY-less lane) printed `Committed 1 path(s): 4d34ebbfda26...` and created commit `chore(prompts): set status pending` without being asked. Recovered with `git reset --soft HEAD~1`, `git restore --staged <path>`, and deleting the probe; `git status --porcelain` empty and HEAD back at `ccd7ee3b8`. This is `status_set._offer_self_commit` behaving as designed (`offer_commit(..., on_unrelated_staged="scope")`), not a defect, and it is exactly why E-05's validation must drive fixtures in a temp repo rather than this checkout. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/status_set.py`: replace the re-listed `"prompts"` entry of `TYPE_STATUSES` with a set
   DERIVED from `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]` plus the retained `done` alias, carrying a
   comment in the shape the `specs` and `backlog` entries already use, and naming this item as the bug the
   stale copy caused. Resolve the `pending` alias per OQ-01 in the same edit. (E-01)
2. `agent_workflows/prompts.py`: add a status writer for the single metadata comment, beside
   `inject_metadata_id6` and `render_metadata_comment`, idempotent and refusing to mint a comment that is
   absent. (E-02)
3. `agent_workflows/status_set.py`: branch `apply_status_change`'s front-matter write on
   `rec.record_type == "prompts"` to use that writer instead of the bullet fallback, and read a prompt's
   current status from the comment so `old_status` stops defaulting to `draft` (F-08). (E-02)
4. `agent_workflows/cli.py`: register `prompts_sub.add_parser("set", ...)` with the declared flag surface
   plus `--dir`/`--yes`; update `command_surface.py`'s `prompts set` `legacy_flags` to match. (E-03)
5. `agent_workflows/cli.py` and `docs/artifact-lifecycles.md`: correct the family `help`/`description`/
   `epilog` to describe two verbs and the three-value exit contract, and name both spellings at the two
   doc sites, leaving the bucket table and mermaid diagram untouched. (E-04)
6. `tests/test_prompts_set_surface.py` (new), `tests/test_status_set.py` +
   `tests/test_exit_contract_conformance.py` (re-pointed docstrings and one added case), and the four
   vocabulary-pinning prompt tests in `tests/test_status_set.py` and
   `tests/test_status_set_descriptive_safety.py` re-targeted to real buckets. (E-05, E-06)

## Deferred / out of scope (with reason)

- **THE DUPLICATE BACKLOG ITEM `68sur3` IS ALREADY CARRIED ELSEWHERE, so this plan does not resolve it.**
  It files the same defect as `um8ikz` (F-12) and is `graduated` with `- Blocks-Release: next` to pending
  plan `gm9baj`, which owns the declared-but-absent leaf GATE while leaving the registration to this plan
  (its Scope `OUT`). With both plans executed the item closes through the standard HANDOFF route on its
  own carrier. This plan must not edit the item (E-07).
  - Carrier: gm9baj
- `aw prompts check` IS NOT IMPLEMENTED AND IS NOT COMING, so do not add it and do not cite its spec as
  live authority. Approved spec `20260808-1958-01-prompt-purity-lint` is now in
  `.aw/records/specs/superseded/` and backlog item `kkzgrk` records the maintainer's 2026-09-26 decision
  verbatim: "DECLINED by maintainer 2026-09-26 (retired, not implemented): no prompt-purity gate," with
  plan `mi4s9f` retired `not-executed`. Plan `iyi4hc`'s review (PR-002) records that two of its checklist
  items called that retired verb and had to be removed. The purity CONVENTION remains live via
  `.aw/records/prompts/README.md` and the three `check.prompt-*` rules; only the dedicated lint is dead.
  - Carrier-Declined: Nothing is owed. The verb was declined by an explicit maintainer decision with a
    stated reason and its plan and spec are both retired; filing a carrier would re-open a human decision.
- **THE SHARED SETTER'S OTHER TREES ARE NOT TOUCHED.** E-01 narrows one dict entry and E-02 adds a
  `record_type == "prompts"` branch; `plans`, `specs`, `backlog`, `releases`, `research` and `other` keep
  their vocabularies and their bullet/YAML writers byte-unchanged. This is deliberate: pending plan
  `xhr0dj` records that `status_set.run_set_command` serves five trees at once "so a guard there changes
  five trees in one edit", and the same caution applies to a writer change.
  - Carrier-Declined: Nothing is owed; no other tree has the defect. The bullet writer is CORRECT for
    every type whose contract is front-matter bullets, which is every type except prompts.
- THE `set` DISPATCH UNIFICATION IS NOT DONE HERE. Spec `wy9aru` rules `status_set` the canonical engine
  and the `setdisp` Set (`63zo2f` and five children) makes `backlog.run_set`/`specs.run_set` thin
  adapters. This plan ADDS a caller to the already-canonical engine, which is aligned with that direction
  and does not depend on it; it deliberately does not reorder, merge or re-route any existing path. The
  carrier below owns the unification and is unaffected by this plan either way.
  - Carrier: 63zo2f
- `status_set`'s inability to read a prompt's `Id:` and `Set:` from the metadata comment is fixed only as
  far as STATUS requires (F-08). The `id6`/`set_id` fields of an `ArtifactRecord` for a prompt stay
  `None`, because F-09 measured that selector matching does not depend on them and plan `3b01h9` already
  fixed the reader asymmetry on the surface where it was user-visible (`aw find`). Widening the record
  reader is a separate change with its own blast radius across every `inventory_all_artifacts` consumer.
  - Carrier-Declined: Nothing is owed for THIS plan's correctness. No user-visible symptom remains that
    this plan leaves behind: the display/filter half shipped in `3b01h9`, and the status half ships here.
- NO NEW BUCKET, NO RENAMED BUCKET, AND NO CHANGE TO THE ATTENTION CLASS MAPPING. The five buckets and
  `attention_contract._PROMPTS_MAP` are the independent corroboration E-01 relies on (F-03); changing
  either would remove the evidence the vocabulary narrowing rests on.
  - Carrier-Declined: Nothing is owed; no defect was measured in either.

## Scope check

- Over-scope: none. Every declared path is edited: `cli.py` (registration + family prose), `status_set.py`
  (vocabulary + prompts write branch), `prompts.py` (the comment status writer), `command_surface.py`
  (the `prompts set` `legacy_flags` tuple, per E-03), `tests/test_status_set.py` (re-pointed docstring +
  added typed-spelling case), `tests/test_exit_contract_conformance.py` (re-pointed docstring census),
  `tests/test_prompts_set_surface.py` (new), `tests/test_status_set_descriptive_safety.py` (one prompt
  fixture status re-pointed, per E-06), and `docs/artifact-lifecycles.md` (two spelling sites). The
  `68sur3` backlog file is NOT declared: it is already graduated to `gm9baj` and this plan does not edit
  it (E-07). The only conditional out-of-declared path is `gm9baj`'s allow-set entry (E-07), justified at
  finalize if touched.
- Under-scope: `check_engine.py` is NOT
  edited, so the three `check.prompt-*` rules are consumed as the oracle for E-02 rather than changed.
  `attention.py`, `attention_contract.py`, `record_placement.py` and `lifecycle_dirs.py` are NOT edited;
  E-01 reads the last of these rather than modifying it. `tests/conformance_matrix.py` is NOT edited: its
  `declared_absent` list shrinks as a RESULT of E-03, which is the observable V-03 asserts.

## Required tests / validation

- `python3 -m pytest tests/test_prompts_set_surface.py tests/test_status_set.py
  tests/test_exit_contract_conformance.py tests/test_command_surface_declarations.py
  tests/test_agent_surface_conformance.py` must pass, with the new module's cases demonstrated to FAIL on
  pre-change code (stash the production edits, run, paste the failures, restore).
- The bare full suite (`python3 -m pytest`) must show no failed node absent from the pre-edit `<baseline>`
  recorded in E-01 (each new one either shown unrelated by a passing isolated re-run, pasted, or the item
  fails). Do NOT add flags: `addopts` already
  supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`.
- `aw check prompts` must report zero errors and zero warnings on the real tree after a real transition of
  a real prompt, and the transitioned prompt must be reverted afterwards (it is tracked content, not a
  fixture). Prefer a temp-repo fixture; if the real tree is used, note F-14's self-commit behavior.
- `conformance_matrix.build_matrix(cli._build_parser()).declared_absent` must no longer contain
  `prompts set`, and `undeclared` must stay `[]`.

## Spec / documentation sync

- NO SPEC IS AMENDED, and the reason is specific rather than a default. The uniform naming spec
  (`20260817-2147-01`, `implemented`) governs prompt FILENAMES and is untouched. The purity spec
  (`20260808-1958-01`) is `superseded` and must not be edited; its convention is cited through
  `.aw/records/prompts/README.md` instead, which is what plan `iyi4hc`'s review required after PR-003
  found a plan resting an invasive edit on that retired contract.
- `wy9aru` (`to-review`) is NOT amended either, though this plan touches its subject matter. Its Section
  3a non-goals already say "Both spellings keep working, with the same arguments, and no verb is renamed
  or removed"; ADDING a registration for a verb its own E-3 row records as dead is consistent with that
  and with its C5 flag-convergence `SHOULD`. Its E-3 row and its carrier table row for `68sur3` become
  historical once this executes, which is what a `## Workflow history` note on that spec is for, not a
  body edit to a spec under review.
- `docs/artifact-lifecycles.md` IS edited at two sites (E-04). `.aw/records/prompts/README.md` is NOT
  edited: it documents the lifecycle, the buckets and the metadata convention, all of which this plan
  CONFORMS to rather than changes, and it names `aw prompts new` without claiming it is the only verb.

## Open questions

### OQ-01: should the `pending -> to-review` alias for prompts be re-pointed to `pending`, or removed?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RE-POINT IT, resolved from repository evidence rather than deferred.
  `normalize_target_status` maps `pending -> to-review` for `record_type in ("plans", "prompts")`, which is
  correct for plans (`pending/` is the plans DIRECTORY and `to-review` is its readiness status, so the
  alias translates a directory name into a status) and incorrect for prompts, where `pending` IS the status
  and `to-review` names nothing: it appears in neither
  `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]` nor `attention_contract.CLASS_MAPS["prompts"]`, and no
  tracked prompt carries it. All 17 prompts carry `pending`, `executed` or `superseded` in their metadata
  comment. So for prompts the alias must become the IDENTITY (`pending -> pending`), which is achieved by
  restricting the existing `pending` branch to `plans` and letting the derived set carry `pending` as a
  real status. Removing the token instead would refuse the single most common prompt status and break
  `aw prompts new`'s own default (`prompts.DEFAULT_STATUS = "pending"`). The `done -> executed` alias is
  UNAFFECTED and stays for both types; `.aw/records/prompts/README.md` documents `done/` as an accepted
  alias for `executed/`.

### OQ-02: should a prompt with no metadata comment gain one when its status is set?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: NO, resolved by following the shipped precedent exactly.
  `prompts.inject_metadata_id6` returns a commentless file UNCHANGED and its docstring states why: minting
  a comment "would ADD a line above the body of a file whose purity this function exists to protect", and
  it records that 6 of 17 measured prompts legitimately had none. The status writer adopts the same
  posture: the transition still RELOCATES the file (the directory is the authoritative lifecycle per
  `.aw/records/prompts/README.md`) and reports plainly that the status lives in the directory only. This
  also keeps E-02 from being a silent mass edit of grandfathered files. Note that all 17 tracked prompts
  DO carry a comment today (measured), so this path is defensive rather than hot; `create_prompt` in
  `tests/test_status_set.py` builds a commentless bullet-shaped fixture, which is the shape that exercises
  it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: Paste `python3 -c "from agent_workflows import status_set as S; print(sorted(S.TYPE_STATUSES['prompts']))"`
    showing the five bucket names plus the retained alias(es) and NOTHING else, beside the pre-change
    eleven-token output from F-04 for contrast. Paste the full refusal text of `aw set prompts draft <id6>`
    showing a nonzero exit and showing the enumerated valid set in the message is the NARROWED one (a bare
    exit code is not sufficient: it would pass even if something else refused). Paste `aw set prompts
    executed <id6>` still succeeding, and `aw set prompts pending <id6>` resolving per OQ-01 to the
    `pending` bucket with `- Status`/comment reading `pending` and NOT `to-review`. Paste a one-line
    demonstration that the set is DERIVED, by showing the prompts entry equals
    `set(lifecycle_dirs.LIFECYCLE_SUBDIRS['prompts']) | {'done'}` computed at runtime, not by quoting the
    source line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: On a prompt minted by `aw prompts new` and given a body, paste the file content
    BEFORE and AFTER `aw prompts set executed <id6>`, showing: the first line is still the metadata
    comment, its `Status:` field now reads `executed`, the body is byte-identical (paste a `sha256` of the
    body region or a `diff` showing only the comment line and the history section changed), and `grep -c
    '^- Status:' <file>` is **0**. Paste `aw check prompts` reporting `errors 0  warnings 0` on that file,
    contrasted with the F-07 measurements (`check.prompt-metadata-missing` error and
    `check.prompt-status-mismatch` warning) taken before the fix. Separately paste the commentless-fixture
    case (OQ-02): the file is relocated, gains NO comment, and the command says so rather than failing.
    Paste the `old_status` the transition reports for a prompt whose comment says `pending`, showing it is
    `pending` and not the `draft` F-08 measured.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste `aw prompts set --help` exiting **0** and listing the declared flags
    (`--message`, `--by-human`, `--dry-run`, `--dir`, `--yes`, `--commit`, `--no-commit`), contrasted with F-01's `invalid choice:
    'set' (choose from 'new')`. Paste `aw prompts set executed <id6> --dry-run` previewing and leaving the
    file byte-identical (show the `sha256` unchanged). Paste the output of
    `python3 -c "import sys; sys.path.insert(0,'tests'); from agent_workflows import cli; from
    conformance_matrix import build_matrix; r = build_matrix(cli._build_parser());
    print(r.undeclared, r.declared_absent, r.passing_count())"` showing `undeclared` still `[]`,
    `declared_absent` NO LONGER containing `prompts set`, and `r.rows_for('prompts set')` NON-EMPTY with
    `r.scenarios_for('prompts set')` equal to `set(conformance_matrix.required_scenarios(command_surface.get_declaration('prompts set')))`
    (the leaf's restored coverage rows; 8 scenarios at review, context only; the 1193 total F-02 measured is
    a live count other plans move and is NOT the bar). Paste `aw prompts set` with an
    unrecognized flag exiting 2, so the declared `exit_contract` still holds.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `aw prompts --help` showing `{new,set}` and showing the `OUTPUT & EXITS`
    block naming all three declared exit values. Paste the two edited `docs/artifact-lifecycles.md` lines
    naming both spellings. Paste a `git diff -- docs/artifact-lifecycles.md` confirming the bucket table
    rows and the mermaid block are NOT in the diff. State explicitly that
    `cli._COMMAND_DESCRIPTIONS["prompts"]` was left unedited and why (it was already correct and only
    became true), quoting it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the new module's full run output with per-test names
    (`python3 -m pytest tests/test_prompts_set_surface.py -o addopts="" -v`), showing a case per defect:
    registration, vocabulary refusal with its message, comment-write with body identity, commentless
    fallback, and dry-run byte-identity. Then paste the PRE-CHANGE failure run: revert ONLY this plan's production
    edits (`git stash push -- agent_workflows/cli.py agent_workflows/status_set.py agent_workflows/prompts.py agent_workflows/command_surface.py`,
    never a bare or directory-wide stash in a shared checkout), run the same command, and paste the failures showing the
    registration case raising `SystemExit(2)`/`invalid choice: 'set'`, the vocabulary case ACCEPTING
    `draft`, and the writer case finding a `- Status:` bullet. Restore and confirm `git status
    --porcelain` shows only intended paths. A test that passes both before and after proves nothing and
    must be reworked.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the two corrected docstrings. For `test_help_floor_gate`, paste the MEASURED
    post-change census (the in-process `--help` exit code per declared leaf, summarized as the count
    exiting 0 and the list exiting 2) proving `prompts set` is no longer among the divergent leaves and
    that the new numbers in the docstring are the measured ones and not hand-decremented. Paste
    `python3 -m pytest tests/test_status_set.py tests/test_exit_contract_conformance.py` passing, and
    paste the specific result for
    `test_status_set.py::...::test_a_non_plan_artifact_transition_is_unaffected` showing BOTH spellings
    exercised. Confirm in prose that no assertion was weakened or skipped to accommodate the change, and
    that `create_prompt`'s bullet-shaped fixture was deliberately left intact per E-06. For each of the
    four E-01 vocabulary tests, paste its diff hunk and its passing result, and paste the new mixed-batch
    refusal assertion's passing result showing the `not valid for prompts` message.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste `git diff <pre-edit-sha> -- .aw/records/backlog/` showing NO change to
    `68sur3`'s file, and its front matter showing `- Status: graduated`, `- Graduated-To: declabsent` and
    `- Blocks-Release: next`. State whether `gm9baj` had executed at run time and, if so, paste the deleted
    allow-set entry diff and its `--scope-reason`. Paste the BARE full-suite output
    (`python3 -m pytest`, no added flags) including its `N passed` summary line beside the pre-edit
    `<baseline>` line, showing no failed node absent from `<baseline>`.
    Paste `aw check prompts` and `aw check all` reporting no new findings, and specifically no
    `check.orphaned-live-blocker` or `check.from-backlog-gate-mismatch` naming either item. Paste
    `git status --porcelain` showing only this plan's declared paths modified (plus the conditional
    `gm9baj` allow-set path, if E-07 touched it), and `git diff --cached --name-only` before the commit confirming nothing
    belonging to another party is staged. Paste `aw ipd lint --phase pre-transition` conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution.

EXECUTION CONTRACT. Commit only the paths this plan declares, through `aw commit <plan> -- <paths>`, never
`git add -A` and never a push. Do not create a tag or a release. When reporting that tests passed, paste
the actual runner output; a claim without output is not evidence. Drive validation fixtures in a temp
repository rather than this checkout wherever possible, because `aw set` SELF-COMMITS on this path (F-14)
and a hand probe in the real tree creates a commit nobody asked for.

ONE ORDERING CONSTRAINT IS LOAD-BEARING AND IS NOT NEGOTIABLE: E-01 and E-02 must land BEFORE E-03. The
registration is what makes the surface reachable, and the two defects it would expose (a six-token
over-wide vocabulary, and a writer that corrupts the artifact and breaks its own checker) are measured, not
hypothetical. Registering first would ship a verb that damages the files it is for.

SCOPE FENCE. The declared `- Scope-Paths:` are a DECLARATION so finalize can reconcile what was edited
against what was declared, not a stop condition: if the work genuinely requires another path (for example
`gm9baj`'s allow-set entry, E-07), make the edit and JUSTIFY it at finalize with `--scope-reason`, and
acknowledge any declared-but-unmodified path with `--scope-ack`. DO stop and report for a genuinely unsafe
condition: an unresolvable concurrent edit to `agent_workflows/cli.py` or `agent_workflows/status_set.py`.

POST-GATE LIFECYCLE MOVE. The finalize obligation is unconditional: this plan does not reach
`.aw/records/plans/executed/` until every `E-*` is `performed`, every `V-*` is `pass` with pasted evidence,
and `aw ipd lint --phase pre-transition` conforms. OWNERSHIP IS CONDITIONAL: under `aw oc run` or
`aw agy run` the RUNNER performs the finalize and the lifecycle move, so do not invoke it yourself; when
executed by hand outside a runner, the executor performs it via `aw ipd finalize`. Never hand `git mv` and
never hand-edit `- Status:`. Backlog item `um8ikz` is set `graduated` by the authoring runner, not by
this execution; do not set it `done` by hand. Backlog item `68sur3` is carried by `gm9baj` and is not edited here (E-07).
