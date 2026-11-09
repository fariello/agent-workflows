# IPD: Build the migration chain, the metadata_schema stamp and the read-path schema check

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 5.1 makes the cutover a numbered migration chain with a `metadata_schema` stamp, and 5.3 makes every metadata read refuse an unmigrated repository. None of it exists (`ls agent_workflows/migrations` fails; `project_schema.parse_portable_policy` knows no `metadata_schema` key). Plan `vxevph` owned this as its E-01, one item naming 11 distinct units across five files; research `nj8zdp` guidance (at most about 8 units per item, 8 work Scope-Paths per plan) splits that item into three one-file steps here, in round 3 on 2026-11-09.
- Scope: (1) the `aw check --agent` baseline for `dcerjg` V-16 and the chain module (`agent_workflows/migrations/__init__.py`, `agent_workflows/migrations/chain.py`); (2) the one `require_current_schema` call in `artifact_meta`'s cache-refresh entry point; (3) `metadata_schema` as a round-tripped portable-policy key in `project_schema` and `install_wizard`; (4) the stamp-and-schema half of `tests/test_migrations_chain.py` (from `vxevph` E-05). Everything runs only on test fixtures. EXCLUDES: preflight, journal, sidecar and their tests (`vxevph`); the `aw migrate` CLI (`1vfqdu`); every later step (`dky26u`, `ghhzb6`, `hpedmn`, `o19353`, `dcerjg`).
- Scope-Paths: agent_workflows/migrations/__init__.py, agent_workflows/migrations/chain.py, agent_workflows/artifact_meta.py, agent_workflows/project_schema.py, agent_workflows/install_wizard.py, tests/test_migrations_chain.py, .aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md
- Item-Dependencies: executed:tve77h
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 101
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g8na48

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from vxevph (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The migration chain module and the `metadata_schema` stamp exist, the stamp survives a reinstall, and every `artifact_meta` read checks it, proven on fixtures, so `vxevph` and every later `m0001` part add steps to an existing chain.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The three items E-01 to E-03 together are `vxevph` E-01 verbatim, partitioned by file: E-01 the baseline and the chain module, E-02 the read-path hook, E-03 the policy round trip.

### Task group 1: the chain module

- [ ] E-01 Before any edit, save `aw check --agent` output to `.aw/state/dcerjg/check-before.jsonl` (the `dcerjg` V-16 baseline; this part runs first in the family). Create the package marker `agent_workflows/migrations/__init__.py` and the module `agent_workflows/migrations/chain.py` holding: a `Migration` record (`number`, `name`, `target_schema`, `is_pending(repo) -> bool`, `run(repo, *, apply, force, force_worktree, describer=None)`); an ordered `MIGRATIONS` tuple holding `m0001` (`metadata-v2`, target 2); the constant `CURRENT_METADATA_SCHEMA = 1` (Order 13 flips it to 2 in the cutover commit); `read_metadata_schema(repo)` and `write_metadata_schema(repo, value)` against the `project_context.resolve_project_context` `config_project` path (never a hard-coded `.aw/config/project.json`); `repo_has_legacy_records(repo)` (any record with a `- Field:` bullet block before the first `##` or a `## Workflow history` section, READMEs excluded); and `require_current_schema(repo)` that raises with the exact text "run `aw migrate metadata`" when the stamp, or 1 when absent on a repository with legacy records, is below `CURRENT_METADATA_SCHEMA`. `write_metadata_schema` writes the file atomically (temporary file plus `os.replace`, as `config.stamp_cutovers` does), keeps every other key and its value, and keeps the trailing newline.
  - Depends on: none
  - Expected outcome: in a tmp repository, `write_metadata_schema(repo, 2)` adds `"metadata_schema": 2` to the resolved `project.json` and leaves `schema_version` and every other key unchanged; `require_current_schema` raises the named message when `CURRENT_METADATA_SCHEMA` is 2 and the stamp is absent on a legacy fixture, and returns silently under the shipped value 1.
  - Execution state: pending

### Task group 2: the read-path hook

- [ ] E-02 Call `require_current_schema` from `artifact_meta`'s one cache-refresh entry point (the freshness check that every public read runs first, `tve77h` E-13), so every metadata-reading command reaches it through the one interface (5.3, C5) and no command needs its own call; `aw migrate`, `aw install`, `aw setup`, `aw doctor` and `aw --help` do not read metadata through `artifact_meta` and so never refuse. This is a one-line hook in `agent_workflows/artifact_meta.py`.
  - Depends on: E-01
  - Expected outcome: no command in this repository refuses before the cutover; with `chain.CURRENT_METADATA_SCHEMA` monkeypatched to 2, `artifact_meta.read(<id6>)` on a legacy fixture raises naming `aw migrate metadata` (AC-11 case 1 at the interface; in phase A no CLI command reads through `artifact_meta` yet, so the CLI-level refusal is demonstrated by `cxxmyv` after Orders 08 and 09 have moved the readers).
  - Execution state: pending

### Task group 3: the stamp survives a reinstall

- [ ] E-03 Make `metadata_schema` a documented member of the portable policy: add it to `known_keys` in `project_schema.parse_portable_policy` AND to the fallback `known_proj_keys` set in `install_wizard` (the copy used when `parse_portable_policy` raises), add an optional `metadata_schema: Optional[int]` field to `project_schema.ProjectPolicySchema` that `to_dict` writes when set, and carry the parsed value through the `ProjectPolicySchema(...)` rebuild in `install_wizard`, so a reinstall never drops the stamp. Moving the key from `unknown_fields` to a field without these three edits would silently delete it on the next `aw install`, because `install_wizard` rebuilds `project.json` from named fields plus `unknown_fields`. Keep the trailing newline (`tests/test_install_config_trailing_newline.py`). `parse_local_binding` is not changed: the stamp lives only in the portable `project.json`.
  - Depends on: E-01
  - Expected outcome: a following `aw install` into a repository stamped with `"metadata_schema": 2` keeps `"metadata_schema": 2`; `tests/test_install_config_trailing_newline.py` still passes.
  - Execution state: pending

### Task group 4: tests

- [ ] E-04 Add the stamp-and-schema half of `tests/test_migrations_chain.py` (the `vxevph` E-05 subset for its E-01, moved here), on `tmp_path` fixture repositories built with real `git init`, calling the real functions and asserting on outputs, exit codes and file bytes (no source reading): the stamp write test, the exact refusal text under a patched `CURRENT_METADATA_SCHEMA = 2`, AC-11 case 1 at the interface (`artifact_meta.read` with the constant patched to 2), and the project-schema test that a reinstall keeps the stamp (PR-001). Set `pytestmark = pytest.mark.core`, or `slow` if its slowest test exceeds 2 s in `--durations=10`, named in V-04.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_migrations_chain.py` passes every test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Path roots come from `project_context.resolve_project_context` (`config_project`, `state_durable`, `records`), never `<repo>/.aw/...` literals (spec 4.5, 5.1) (carried from `vxevph` Step 0).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `vxevph` F-02: `rg -n "known_keys\|known_proj_keys\|ProjectPolicySchema\(" agent_workflows/project_schema.py agent_workflows/install_wizard.py`: 8 hits | E-03 touches two files and three edit sites. |
| F-02 | `ipd_lint` IPD-Z603 on `vxevph` (2026-11-09, cutover patched): "E-01 names 11 distinct units" and "plan declares 10 work Scope-Paths" | Splitting E-01 into three one-file items and moving them here brings both plans under the guidance. |

## Proposed changes (ordered, validatable)

1. E-01: baseline and chain module.
2. E-02: read-path hook.
3. E-03: policy round trip.
4. E-04: tests.

## Deferred / out of scope (with reason)

- Preflight, journal, sidecar import, and their test modules.
  - Carrier: vxevph

## Scope check

- Over-scope: none. The `artifact_meta.py` edit is the one `require_current_schema` call in the read path.
- Under-scope: none for `vxevph` E-01 and the stamp half of its E-05.

## Required tests / validation

New module: `tests/test_migrations_chain.py` (`core`, stamp half; `1vfqdu` may add CLI cases in `tests/test_migrate_cli.py`). Existing: `tests/test_install_config_trailing_newline.py`. Gate: bare `python3 -m pytest`, beside the named runs.

## Spec / documentation sync

No spec change; implements `4sd62s` 5.1 (chain, stamp) and the 5.3 refusal mechanism. The CHANGELOG line is written once by `dcerjg` E-16.

## Open questions

### OQ-03: How can `metadata_schema` and the AC-11 refusal ship in phase A without refusing this unmigrated repository?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `vxevph` OQ-03 (from `dcerjg` OQ-03): `require_current_schema` compares against `CURRENT_METADATA_SCHEMA`, which is 1 and an absent stamp counts as 1, so nothing refuses before the cutover; Order 13 sets the constant to 2 in the cutover commit. Tests patch the constant to 2.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/dcerjg/check-before.jsonl` (exists, nonzero) and `rg -n "^(class Migration|MIGRATIONS|CURRENT_METADATA_SCHEMA|def (read_metadata_schema|write_metadata_schema|repo_has_legacy_records|require_current_schema))" agent_workflows/migrations/chain.py` showing each of the seven names once; and the PASSED node ids from `python3 -m pytest -o addopts="" -v tests/test_migrations_chain.py -k "stamp or refusal"` for the stamp-write test (`schema_version` unchanged) and the exact-refusal-text test.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` hunk of `agent_workflows/artifact_meta.py` (one added `require_current_schema` call in the refresh entry point) and the PASSED node id of the test showing `artifact_meta.read` on a legacy fixture with the constant patched to 2 raises naming `aw migrate metadata`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunks adding `metadata_schema` in `agent_workflows/project_schema.py` (`known_keys`, the `ProjectPolicySchema` field, `to_dict`) and `agent_workflows/install_wizard.py` (`known_proj_keys`, the rebuild); the PASSED node id of the reinstall-keeps-stamp test; and `python3 -m pytest -o addopts="" -v tests/test_install_config_trailing_newline.py` with every node id PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_migrations_chain.py --durations=10` with every node id PASSED and the durations table, naming the module `core` or `slow`; and, beside it, the bare `python3 -m pytest` summary line inside the 30 s budget.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: this plan never runs `aw migrate metadata --apply` in this checkout; every test uses a `tmp_path` fixture.

Honesty rule: run the named test modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit g8na48 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize g8na48` itself.
