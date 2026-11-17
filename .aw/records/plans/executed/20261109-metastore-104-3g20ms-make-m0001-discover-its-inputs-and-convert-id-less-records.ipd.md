# IPD: Make m0001 discover its inputs and convert id-less records

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 5.2a requires `aw migrate metadata` to discover its inputs in any repository instead of using this repository's constants (the 34-entry rename map, the 28-id mint list, `wvlk84`), and to convert id-less records (C12 shape c). Plan `g5hpbb` owned this (its E-04, E-05) beside six other items; research `nj8zdp` guidance splits it in round 3 on 2026-11-09.
- Scope: Add `agent_workflows/migrations/m0001_discover.py` with `discover(repo) -> Inventory` and replace every repository-specific constant in the `m0001_*` modules with values computed from it (E-01, from `g5hpbb` E-04); mint ids, statuses, titles and Set/order for id-less records and list unclassifiable files untouched (E-02, from `g5hpbb` E-05). EXCLUDES: the cache changes (`6oi2nu`), layout stage and sidecar expectation (`bv4kkj`), the AC-42 test module and changelog (`g5hpbb`).
- Scope-Paths: agent_workflows/migrations/m0001_discover.py, agent_workflows/migrations/m0001_metadata_v2.py, agent_workflows/migrations/m0001_renames.py, agent_workflows/migrations/m0001_convert.py, agent_workflows/migrations/m0001_verify.py, .aw/records/plans/pending/20261109-metastore-104-3g20ms-make-m0001-discover-its-inputs-and-convert-id-less-records.ipd.md
- Scope-Exceeded: agent_workflows/migrations/chain.py (V-01 requires zero repo-specific template filename literals anywhere in agent_workflows/migrations/ chain.py held prompt-library-template.md and legacy-agents-prompt.md); tests/test_m0001_discover.py (Unit and integration behavioral test coverage for m0001_discover.discover and idless_prose conversion E-01 and E-02)
- Item-Dependencies: executed:dcerjg, executed:9vf2iv, executed:6oi2nu
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 104
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3g20ms

> Written to `.aw/system/workflows/technical-writing/technical-writing.md`. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history
- 2026-11-17 executed (aw agy run model=Gemini-4-Hydrogen-High): aw agy run self-finalize: 3g20ms verified (set metastore, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/migrations/chain.py: V-01 requires zero repo-specific template filename literals anywhere in agent_workflows/migrations/; chain.py held prompt-library-template.md and legacy-agents-prompt.md; out-of-scope tests/test_m0001_discover.py: Unit and integration behavioral test coverage for m0001_discover.discover() and idless_prose conversion (E-01 and E-02)]
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004.
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from g5hpbb (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`m0001` computes its renames, mints and counts from a discovered inventory and converts id-less records, so the same code migrates this repository and any other.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: one migration for every repository

- [x] E-01 (carried verbatim from `g5hpbb` E-04) Add `agent_workflows/migrations/m0001_discover.py`: `discover(repo) -> Inventory` returns every candidate record with its source tree, type, identity (present, or to mint), status source (bullet, YAML, comment, disposition directory), and a reason for every file it cannot classify; whether a sidecar is EXPECTED (5.2a item 5: some record's own history shows a sidecar-writing setter ran) and whether one is present; and whether a legacy layout stage is needed. Replace every repository-specific constant in `m0001_*` (the 34-entry rename map, the 28-id mint list, counts, the `wvlk84` special case) with values computed from this inventory; the measured values for this repository become assertions in `g5hpbb` E-07's this-repository case, not code.
  - Depends on: none
  - Expected outcome: a pasted `rg` over `agent_workflows/migrations/` finds no id6 literal, no record filename and no corpus count; `discover` on this repository reproduces the 34 legacy-name renames and 28 mints that `dcerjg` measured.
  - Execution state: performed

- [x] E-02 (carried verbatim from `g5hpbb` E-05) Convert id-less records (shape c) per 5.2a item 4: mint a repository-unique id6 through `artifact_core.mint_id6`, take `status` from the disposition directory, `title` from the first `# ` line, and Set and order by the 5.2 step 3 rule; record each minted value in the migration journal so a dry run and the apply mint the same id. Files `discover` could not classify are listed in the census with their reason and left byte-identical by `--apply`.
  - Depends on: E-01
  - Expected outcome: on `idless_prose`, the dry-run census lists the prose plan with its minted id6, `executed` status and title, and the unclassifiable file with its reason; after `--apply` the plan has a log and the unclassifiable file is unchanged (`git diff --quiet -- <file>`).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Ids are minted by `artifact_core.mint_id6` (repository-wide collision check) (carried from `dcerjg` Step 0).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Spec 5.2 and plan `dcerjg` are this-repository-specific. | `g5hpbb` F-06: 5.2 step 3 names 34 renames, 28 mints and `wvlk84`. |
| F-02 | Prose plans with no metadata bullets exist in the field. | `g5hpbb` F-03. |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    subgraph S1["Task group 1: Universal repository discovery & id-less conversion"]
        E1["E-01: Add m0001_discover.py and replace hardcoded repo constants with discovered inventory"]
        E2["E-02: Convert id-less records (shape c) and list unclassifiable files untouched"]
    end
    subgraph V["Verification"]
        V1["V-01: Verify zero id6 literals or filename constants in migrations and verify discovery on repo"]
        V2["V-02: Verify dry-run census and applied log for idless_prose fixture with unclassifiable file check"]
    end
    E1 --> V1
    E2 --> V2
```

1. E-01: discovery and constant removal.
2. E-02: id-less conversion.

## Deferred / out of scope (with reason)

- Layout stage, companion backends and the no-sidecar rule; the AC-42 proof.
  - Carrier: g5hpbb

## Scope check

- Over-scope: none. The four existing `m0001_*` modules change only to read discovered values instead of constants.
- Under-scope: none for `g5hpbb` E-04 and E-05; their cases are proven end to end in `g5hpbb` E-07.

## Required tests / validation

Proven by V-01 and V-02 directly; the parameterized AC-42 module `tests/test_m0001_any_repo.py` is `g5hpbb`'s. Existing `tests/test_m0001_renames.py`, `tests/test_m0001_conversion.py` and `tests/test_m0001_roundtrip.py` must still pass (named in V-01).

## Spec / documentation sync

No spec change; implements `4sd62s` 5.2a items 1 and 4.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition) (as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction), name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `rg` over `agent_workflows/migrations/` for id6 literals, record filenames and corpus counts (no hits), and `discover(<this repo>)` reporting 34 legacy-name renames and 28 mints; and `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py tests/test_m0001_conversion.py tests/test_m0001_roundtrip.py` with 0 failed (each module's node ids PASSED).
  - Observed evidence:
    - `rg` check over `agent_workflows/migrations/` for id6 literals, record filenames, and corpus counts (`RG_EXIT=1`, 0 hits):
      ```text
      rg -n '([0-9]{8}-[0-9]{4}-[0-9]{2}-|[0-9]{8}-[a-z0-9-]+-[0-9]{2,3}-[0-9a-z]{6}-|wvlk84|lus9ou|7qx7ys|8q6yr9|4o5lt9|4w7d6s|fwtqr8|wazeo5|06nu85|migrate-existing-plans|assess-bugs-leftover|chatgpt-modular-report|conformance-results|\b34\b|\b466\b)' agent_workflows/migrations/; echo "RG_EXIT=$?"
      RG_EXIT=1
      ```
    - `m0001_discover.discover(Path('.')).format_summary()` on this repository:
      ```text
      Inventory: 3369 records, 1512 reviews, 0 unclassifiable, 43 excluded
        Legacy-name renames: 34 (mints=28, total_mints=28)
        Sidecar: present=False, expected=True (setter 'aw backlog' in backlog/done/20260815-7vd36f-01-7vd36f-ipd-scaffold-clustering-grammar.backlog.md)
        Layout stage needed: False (already on .aw/)
      ```
    - `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py tests/test_m0001_conversion.py tests/test_m0001_roundtrip.py` (`25 passed in 4.24s`):
      ```text
      tests/test_m0001_conversion.py::test_path_history_renamed_plan_records_checkpoint_old_then_rename_new PASSED [  4%]
      tests/test_m0001_conversion.py::test_fields_releases PASSED              [  8%]
      tests/test_m0001_conversion.py::test_excluded_comms_data_readmes_non_5_trees_and_six_templates_byte_identical PASSED [ 12%]
      tests/test_m0001_conversion.py::test_fields_specs PASSED                 [ 16%]
      tests/test_m0001_conversion.py::test_clock_ac19_filename_date_created_day_and_last_history_day PASSED [ 20%]
      tests/test_m0001_conversion.py::test_mirror_and_banner_all_standard_types_plus_fenced_history_guard PASSED [ 24%]
      tests/test_m0001_conversion.py::test_prompt_ac40_case1_commented_and_case2_commentless PASSED [ 28%]
      tests/test_m0001_conversion.py::test_layout_ac32_sequence_sidecar_scope_exceeded_describer_and_sr903 PASSED [ 32%]
      tests/test_m0001_conversion.py::test_fields_plans_ipd PASSED             [ 36%]
      tests/test_m0001_conversion.py::test_fields_backlog PASSED               [ 40%]
      tests/test_m0001_conversion.py::test_fields_prompts PASSED               [ 44%]
      tests/test_m0001_roundtrip.py::test_census_refuses_unknown_field_unparseable_dep_and_missing_description_on_apply PASSED [ 48%]
      tests/test_m0001_roundtrip.py::test_census_no_sidecar_none_expected_skips_absent_templates_and_lists_fields PASSED [ 52%]
      tests/test_m0001_roundtrip.py::test_step6_stamp_and_rollback_restores_project_json PASSED [ 56%]
      tests/test_m0001_roundtrip.py::test_roundtrip_step3_rewritten_citations_and_prompt_hr PASSED [ 60%]
      tests/test_m0001_roundtrip.py::test_roundtrip_long_and_control_char_history_lines_and_writer_refusal PASSED [ 64%]
      tests/test_m0001_roundtrip.py::test_roundtrip_leak_sanitizer_fail_refuses_apply PASSED [ 68%]
      tests/test_m0001_roundtrip.py::test_step7_commit_with_installed_precommit_hooks_and_second_apply_idempotence PASSED [ 72%]
      tests/test_m0001_renames.py::test_build_rename_map_mints_reuses_journal_and_honors_logged_order PASSED [ 76%]
      tests/test_m0001_renames.py::test_apply_step3_protected_bytes_moves_idempotency_and_resume PASSED [ 80%]
      tests/test_m0001_renames.py::test_plan_citation_rewrites_protects_spans_exemptions_fences_and_sums_counts PASSED [ 84%]
      tests/test_m0001_renames.py::test_classify_name_legacy_6letter_slug_vs_clustered_4digit_set PASSED [ 88%]
      tests/test_m0001_renames.py::test_build_rename_map_refusals_and_unmapped_duplicates PASSED [ 92%]
      tests/test_m0001_renames.py::test_plan_citation_rewrites_guard_and_gitignored_scratch_root PASSED [ 96%]
      tests/test_m0001_renames.py::test_m0001_metadata_v2_step3_wiring_dry_run_apply_rollback_and_missing_root PASSED [100%]
      25 passed in 4.24s
      ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the `idless_prose` dry-run census lines for the prose plan (minted id6, status `executed`, title) and the unclassifiable file (reason); then, after `--apply`, its log's first event and `git diff --quiet -- <unclassifiable file>; echo $?` printing `0`. Produced by `aw migrate metadata` (E-02 code path).
  - Observed evidence:
    - `aw migrate metadata` dry run on `idless_prose` fixture (code path `m0001_metadata_v2.run` -> `m0001_renames.build_rename_map` -> `m0001_verify.build_field_census`/`format_census`):
      ```text
      INFO     Renames:       1 entries (1 minted, 0 preserved)
        7qoc6y (minted): plans/executed/20260715-prose-migration-ipd.md -> plans/executed/20260715-7qoc6y-01-7qoc6y-prose-migration-ipd.ipd.md
        Minted id-less records (1):
          - 7qoc6y: plans/executed/20260715-prose-migration-ipd.md -> plans/executed/20260715-7qoc6y-01-7qoc6y-prose-migration-ipd.ipd.md (type=ipd, status=executed [disposition], title='Implementation Plan Document (IPD) - Synthetic Prose Plan')
        Unclassifiable files (left untouched, 1):
          - notes/scratch.md: unrecognized directory 'notes/' and no record type facet or metadata marker
      OK       round trip: pass (replayed=1, reviews=0, leak_fail=0, leak_warn=0)
      ```
    - After `aw migrate metadata --apply` (`commit f784a38b3ecee0194e912930b13685e60cd6b8c2`), `.aw/records/meta/7qoc6y.jsonl` first event and unclassifiable diff check:
      ```text
      {"actor":{"tool":"aw migrate metadata"},"append":0,"at":"2026-11-17T21:39:02Z","fields":{"description_model":"stub","description_prompt_version":"v1","description_source":"generated","filename_date":"2026-07-15","id":"7qoc6y","order":1,"set":"7qoc6y","short_description":"Synthetic prose plan without metadata bullets.","status":"executed","title":"Implementation Plan Document (IPD) - Synthetic Prose Plan","type":"ipd"},"op":"checkpoint","path":"plans/executed/20260715-prose-migration-ipd.md","seq":0,"v":1}
      git diff --quiet -- .aw/records/notes/scratch.md; echo $? -> 0
      ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. A narrow safety stop applies if prerequisite metastore symbols from `dcerjg`, `9vf2iv`, or `6oi2nu` are absent. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: never run `aw migrate metadata --apply` on this checkout or any of the maintainer's other repositories; only on generated fixtures.

Honesty rule: paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 3g20ms -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 3g20ms` itself.
