# IPD: Write short_description at creation for backlog, specs and releases

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.2 SHORT DESCRIPTION and AC-36 case 1 require every creating command to accept `--summary` and write it as `short_description`. `aw backlog new`, `aw specs new` and `aw releases new` already take `--summary` (F-01) but write it only into body text. This is part of `6e93gt` (itself part of `xexn45`), split 2026-11-09 so each item names one command.
- Scope: Make `aw backlog new`, `aw specs new` and `aw releases new` write `--summary` as `short_description` in their `create` event (`6e93gt` E-01, the backlog, specs and releases subset), and create the shared test module `tests/test_writers_create_summary.py`. EXCLUDES: research and adopt (`bir7xm`), plan scaffold and prompts with `ipd_schema.META_RECOGNIZED` (`py2vu9`), `aw describe` (`h06gs7`).
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/releases.py, agent_workflows/artifact_meta.py, tests/test_writers_create_summary.py, .aw/records/plans/pending/20261109-metastore-124-fekdwv-write-short-description-at-creation-for-backlog-specs-and-re.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94, executed:n5sxxk
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 124
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: fekdwv

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 6e93gt (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw backlog new`, `aw specs new` and `aw releases new` store their `--summary` as `short_description` through `artifact_meta`, with the same refusals as today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: short description at creation

- [ ] E-01 Create `tests/test_writers_create_summary.py` (fixtures in `tmp_path`, real CLI) and make `aw backlog new --summary` write the value as `short_description` (`6e93gt` E-01, backlog subset): in `backlog.run_new`, the value is written as `short_description` in the `create` event when it passes `attention_contract.refuse_unsafe_descriptive` at `MAX_DESCRIPTIVE_LEN` (300); in phase B the legacy writer renders the field as a `- Short-Description:` bullet. Because backlog has no unknown-bullet check, the gate is a test: the module's backlog case runs `aw check all --agent` on its fixture and asserts no diagnostic names the new field.
  - Depends on: none
  - Expected outcome: for `aw backlog new`, `--summary "Adds a widget."` then `artifact_meta.read(<id6>).fields["short_description"] == "Adds a widget."`; a 301-character value, a newline value and a control-character value each exit nonzero with no file written.
  - Execution state: pending

- [ ] E-02 Make `aw specs new --summary` write `short_description` (`6e93gt` E-01, specs subset): in `specs.run_new`, the value is written as `short_description` in the `create` event when it passes `attention_contract.refuse_unsafe_descriptive` at `MAX_DESCRIPTIVE_LEN` (300); in phase B the legacy writer renders the field as a `- Short-Description:` bullet. A `--summary` over 300 characters (still accepted up to `MAX_PROSE_DESCRIPTIVE_LEN` through `specs._refuse_unsafe_descriptive(..., prose=True)` today) is written only to the body summary and writes no `short_description` (4.2 SHORT DESCRIPTION). Add the cases to `tests/test_writers_create_summary.py`.
  - Depends on: E-01
  - Expected outcome: for `aw specs new`, `--summary "Adds a widget."` then `artifact_meta.read(<id6>).fields["short_description"] == "Adds a widget."`; a 301-character value, a newline value and a control-character value each exit nonzero with no file written; a 400-character `aw specs new --summary` writes the body summary and no `short_description`.
  - Execution state: pending

- [ ] E-03 Make `aw releases new --summary` write `short_description` (`6e93gt` E-01, releases subset): in `releases.run_new`, the value is written as `short_description` in the `create` event when it passes `attention_contract.refuse_unsafe_descriptive` at `MAX_DESCRIPTIVE_LEN` (300); in phase B the legacy writer renders the field as a `- Short-Description:` bullet. Add the cases to `tests/test_writers_create_summary.py`.
  - Depends on: E-01
  - Expected outcome: for `aw releases new`, `--summary "Adds a widget."` then `artifact_meta.read(<id6>).fields["short_description"] == "Adds a widget."`; a 301-character value, a newline value and a control-character value each exit nonzero with no file written.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- Descriptive refusals: `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300 and `MAX_PROSE_DESCRIPTIVE_LEN` 4300; `specs._refuse_unsafe_descriptive(..., prose=True)` is the spec `--summary` path.
- Recognized plan bullets are `ipd_schema.META_RECOGNIZED`; an unrecognized bullet is lint error `IPD-M103` (`ipd_lint.C_META_UNKNOWN`). The other types have no unknown-bullet check today (`specs.validate_spec`, `backlog._render_item`, `releases.validate_release`; research validates only its required YAML keys in `research_contract.FRONTMATTER_FIELDS`).

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | `rg -n "\"--summary\"" agent_workflows/cli.py`: research new, research comparison, backlog new, specs new, releases new and adopt carry it; scaffold and prompts new do not | These three commands need no new option, only the new field in their `create` event. |
| F-02 | `agent_workflows/artifact_meta.py` already maps `Short-Description` to `short_description` | No new mapping should be needed; the file is declared in case one is. |

## Proposed changes (ordered, validatable)

1. Create the test module and wire backlog (E-01).
2. Wire specs, with the over-300 rule (E-02).
3. Wire releases (E-03).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` reconciliation of the `--summary` options and the `CHANGELOG.md` line, and the full gates of the writer move.
  - Carrier: xexn45
- `--summary` for research and adopt.
  - Carrier: bir7xm
- `--summary` for plan scaffold and prompts, and the `ipd_schema.META_RECOGNIZED` entry.
  - Carrier: py2vu9
- The `aw describe` setter.
  - Carrier: h06gs7

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared in case a mapping is needed; acknowledge it at finalize when unmodified.

## Required tests / validation

New core test module: `tests/test_writers_create_summary.py` (created here; `bir7xm`, `py2vu9` and `h06gs7` add cases). Contributes to `4sd62s` AC-36 case 1 (`cxxmyv` re-demonstrates the full criterion).

## Spec / documentation sync

None. Implements `4sd62s` 4.2 SHORT DESCRIPTION as written; `xexn45` E-14 adds the documentation and changelog lines.

## Open questions

### OQ-02: How does `short_description` appear on disk in phase B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: As a `- Short-Description:` bullet (a `Short-Description:` key inside a prompt's comment; a `short-description:` YAML key in research front matter), registered as a recognized field in `ipd_schema.META_RECOGNIZED` and proven unflagged for the other types by `aw check all --agent`. Evidence: phase B has one on-disk format (C10a), the legacy loader reads bullets (tve77h E-11) so the value survives a cache rebuild, and an unregistered bullet is lint error `IPD-M103` on plans. The alternative (no on-disk form until the cutover) would make AC-36 case 1 untestable through `read()` after a cache deletion. The migration (dcerjg) maps the bullet to `short_description` with `description_source` absent (written by a command, not generated), and the census lists it. Recommendation strength: strong.
- Note: carried unchanged from `6e93gt` (originally `xexn45`) with its id, so the item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k backlog` all PASSED, naming the `tests/test_writers_create_summary.py` cases for `aw backlog new`: the stored-value case (quote its `artifact_meta.read(id6).fields["short_description"]` assertion), the 301-character, newline and control-character refusal cases (each asserting a nonzero exit code and `git status --porcelain` empty), and the `aw check all --agent` case asserting no diagnostic names the new field.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k specs` all PASSED, naming the `tests/test_writers_create_summary.py` cases for `aw specs new`: the stored-value case (quote its `artifact_meta.read(id6).fields["short_description"]` assertion), the 301-character, newline and control-character refusal cases (each asserting a nonzero exit code and `git status --porcelain` empty), and the `aw check all --agent` case asserting no diagnostic names the new field, plus the 400-character case asserting no `short_description` and the body summary present.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k releases` all PASSED, naming the `tests/test_writers_create_summary.py` cases for `aw releases new`: the stored-value case (quote its `artifact_meta.read(id6).fields["short_description"]` assertion), the 301-character, newline and control-character refusal cases (each asserting a nonzero exit code and `git status --porcelain` empty), and the `aw check all --agent` case asserting no diagnostic names the new field.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit fekdwv -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize fekdwv` itself.
