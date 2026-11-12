# Review findings: plan g8na48

- Subject-Id: g8na48
- Subject-Type: ipd
- Reviewed-At: 2026-11-12
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `aca012dc9` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `3` info advisories: `IPD-Z602` on `E-04` line 60 and two `IPD-C802` em-dash hits on line 114), and the pinned existing test modules (`tests/test_install_config_trailing_newline.py` and `tests/test_artifact_meta_read.py`) passed (`16 passed`). During revision, `aw ipd sync --apply` assigned `E-05` and `V-05` (advancing `- Highest E allocated:` from `04` to `05` so `project_schema.py` and `install_wizard.py` each have one single-module item), Pass 2 re-checked `E-01..E-05` and `V-01..V-05`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope, Scope check | Claimed one `require_current_schema` call in `check_freshness` covers every read and omitted cross-lane baseline SHA | Covers both `check_freshness` and `read_at` via `_require_schema`, plus tracked baseline SHA/count in `F-03` | PR-002, PR-004. |
| E-01, Step 0 | Directed `read_metadata_schema` and `repo_has_legacy_records` at `resolve_project_context` (`logical_roots["records"]` defaults to `<AW_HOME>` on unconfigured repos), detected only `- Field:` / `## Workflow history`, and left `m0001.run` import behavior unspecified | Uses `project_config_dir` / `config_project` and `[records_root or project_records_dir(repo), repo / ".agents"]`, detects all non-v2-mirror records across `4sd62s` C12 shapes (a)-(e), defines `MetadataSchemaError(RuntimeError)`, and specifies lazy `m0001_metadata_v2.run` delegation | PR-001, PR-002, PR-005. |
| E-02 | Hooked only `check_freshness`, missed `read_at`, did not isolate bare `logical_roots` test stubs from `cwd`, and falsely claimed no CLI command reads through `artifact_meta` yet | Wires `_require_schema` into `check_freshness` (before `!records_root.exists()`) and `read_at`, isolates `tmp_path` test stubs, and accurately cites `1ajqaa` (`meta_cli`) | PR-002, PR-006. |
| E-03 -> E-03, E-05 | Single multi-file item omitting `install_wizard` `except ValueError:` fallback extraction and `parse_portable_policy` int/bool validation | Split via `aw ipd sync --apply` into `E-03` (`project_schema.py` with positive-int non-bool validation) and `E-05` (`install_wizard.py` preserving `existing_metadata_schema` in both `try` and `except ValueError` branches) | PR-003, PR-006 (`IPD-Z602`/`IPD-Z603`). |
| E-04 | Triggered `IPD-Z602` and contained unexplained `(PR-001)` citation | Structured cleanly around `Create tests/test_migrations_chain.py` covering AC-11 cases 1-3, `.agents/`, `read_at`, v2 `tmp_path` stubs, and normal/fallback reinstalls (`dcerjg` review finding `PR-001`) | PR-001..PR-003, PR-006. |
| Findings (`F-01`..`F-03`), Proposed changes | Omitted cross-lane baseline row and had no architecture diagram | Added `F-03` for baseline SHA/pair count and added a Mermaid `flowchart TD` diagram | PR-004, Technical Writing Standard Requirement 12. |
| OQ-03, Validation preamble (`V-01..V-05`), Approval gate | Omitted `Recommendation strength:` in `OQ-03`, contained two em dashes (`IPD-C802`), and omitted concurrent-edit stop sentence | Added `Recommendation strength: strong.`, replaced em dashes with commas, mapped `V-01..V-05` 1:1 to `E-01..E-05`, and added unsafe-condition stop sentence | Proofreading (`IPD-C802`), Step S5, Step S7. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `agent_workflows/migrations/chain.py` (`Migration`, `MIGRATIONS`, `CURRENT_METADATA_SCHEMA`, `MetadataSchemaError`, `read_metadata_schema`, `write_metadata_schema`, `repo_has_legacy_records`, `require_current_schema`) and `ProjectPolicySchema.metadata_schema` define public cross-plan contracts consumed by `vxevph`, `1vfqdu`, `cxxmyv`, `x1mmdp`, and `dcerjg`.
2. Yes. `write_metadata_schema` and `install_wizard.persist_project_policy` mutate portable `project.json` atomically, and `artifact_meta._require_schema` gates every metadata read across `check_freshness` and `read_at`.
3. Yes. Five `E-*` items across four subsystems (`migrations`, `artifact_meta`, `project_schema`/`install_wizard`, and `tests/test_migrations_chain.py`).
4. No. All seven `- Scope-Paths:` entries are explicit file paths, not directory globs.
5. Yes. Dropping `metadata_schema` during a reinstall or misresolving unconfigured/legacy roots either breaks migrated repositories after `aw install` or silently skips the AC-11 refusal on unmigrated `.aw/records/` and `.agents/` repositories.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C5, C9, C10a, C12, AC-10, AC-11, AC-18, AC-22, AC-27, AC-28, AC-42, sections 4.1, 4.1a, 4.5, 4.9.2, 5.1, 5.2, 5.2a, 5.3, 7); orchestrator `63ib9r`; sibling plans `vxevph`, `1vfqdu`, `dcerjg` (and `dcerjg.review.md`), `cxxmyv`, `x1mmdp`; executed dependencies/readers `tve77h` and `1ajqaa`; production modules `agent_workflows/artifact_meta.py`, `agent_workflows/project_context.py`, `agent_workflows/project_schema.py`, `agent_workflows/install_wizard.py`, `agent_workflows/config.py`, `agent_workflows/selectors.py`, `agent_workflows/meta_cli.py`; test modules `tests/test_install_config_trailing_newline.py` and `tests/test_artifact_meta_*.py`.
- Found root-resolution and legacy-detection bug (`PR-001`): empirical probe of `project_context.resolve_project_context(target_repo=str(tmp_repo))` confirmed that on an unconfigured repository (no `project.json`, AC-11 cases 1 and 3), `ctx.logical_roots["records"]` resolves to `<AW_HOME>/projects/<pid>/records` (`RecordsBackend.HOME` default), missing `<repo>/.aw/records` and `<repo>/.agents/`, while `config_project` lives in `ctx.physical_classes["config_project"]` (or `project_context.project_config_dir(repo) / "project.json"`). In addition, checking only `- Field:` bullets and `## Workflow history` misses prose-only `.agents/` records (`C12` shape (c)), legacy `<!-- aw-prompt:` / comment-less staged prompts, and multi-key YAML research files (`4sd62s` 4.1, 5.2a). Fixed in `E-01` and `Step 0` using `project_config_dir`, `[records_root or project_records_dir(repo), repo / ".agents"]`, and `artifact_meta`'s three v2 mirror parsers (`parse_artifact_mirror`, `parse_review_mirror`, `parse_staged_prompt_mirror`).
- Found three `artifact_meta` read-path defects (`PR-002`): (1) `artifact_meta.read_at` (`agent_workflows/artifact_meta.py:3540`) does not call `check_freshness`, and `check_freshness` (`agent_workflows/artifact_meta.py:3020`) returns early when `records_root` is absent (missing `.agents/`-only repositories); (2) all 6 `tests/test_artifact_meta_*.py` modules pass bare `logical_roots`-only `Ctx` stubs on `tmp_path` without `target_repo`, so falling back to `os.getcwd()` would inspect the host checkout; and (3) `meta_cli._collect` (`agent_workflows/meta_cli.py:271`) catches `except ValueError:` as an `invalid-record` defect. Fixed by raising `MetadataSchemaError(RuntimeError)` and calling `_require_schema` in both `check_freshness` (before the early return) and `read_at` without `cwd` fallback.
- Found reinstall stamp-loss bug on fallback rebuild (`PR-003`): in `install_wizard.persist_project_policy` (`agent_workflows/install_wizard.py:1339`), when `parse_portable_policy(raw_proj)` raises `ValueError` on a malformed sibling key, the `except ValueError:` branch strips every key in `known_proj_keys` out of `existing_unknown` and manually extracts `existing_cutovers`, `existing_setids`, and `existing_consent`. Adding `"metadata_schema"` to `known_proj_keys` without extracting `existing_metadata_schema` in that `except ValueError:` branch silently deletes the stamp. Fixed in `E-03` and `E-05`.
- Found import-order gap with `vxevph` (`PR-005`): `g8na48` defines `MIGRATIONS` holding `m0001`, whereas `vxevph` (which depends on `executed:g8na48` and does not include `chain.py` in its `- Scope-Paths:`) creates `agent_workflows/migrations/m0001_metadata_v2.py`. Specified `m0001.is_pending` over `chain.py` functions and lazy delegation to `m0001_metadata_v2.run` inside `m0001.run`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5` after `aw ipd sync --apply`), dependency graph (`E-01` -> `E-02`, `E-03`; `E-03` -> `E-05`; `E-01, E-02, E-03, E-05` -> `E-04`), `- Scope-Paths:` completeness (all 7 paths match planned edits), and runtime reachability of every `V-*` check.
- Found cross-lane gitignored baseline gap (`PR-004`): `.aw/state/dcerjg/check-before.jsonl` is gitignored and disappears between `g8na48`'s isolated worktree lane and `dcerjg`'s later isolated worktree lane. Added `F-03` (and `V-01` check) to record the pre-edit `HEAD` SHA and `(location, rule)` pair count in tracked plan text so `dcerjg` V-16 can regenerate `check-before.jsonl` deterministically if run in a separate lane.

### Step R3

- Checked: atomic `project.json` writes (`os.replace` on a sibling temporary file in the target directory), fail-closed `metadata_schema` integer validation (`isinstance(val, int) and not isinstance(val, bool) and val >= 1` because `isinstance(True, int)` is `True` in Python), `MetadataSchemaError(RuntimeError)` propagation past `meta_cli._collect`'s `except ValueError:` handler, and zero host-checkout or `<AW_HOME>` leakage on `tmp_path` fixtures.

### Step R4

- Checked: phase-A/phase-B read-path performance (when `stamp >= CURRENT_METADATA_SCHEMA` or `stamp is None and CURRENT_METADATA_SCHEMA <= 1`, `require_current_schema` returns in O(1) without walking the 4,400-record tree, keeping bare `python3 -m pytest` well inside the 30 s budget), AC-11 cases 1-3, C12 shapes (a)-(e), outcome-based test assertions (no source inspection), and single-module right-sizing (`E-01`..`E-05`).

### Step R5

- Checked: QA/QC (`V-01..V-05` falsifiability across AC-11 cases 1-3, `.agents/`, `read_at`, and fallback reinstall), Architect (clean boundary between `chain.py`, `artifact_meta`, `project_schema`/`install_wizard`, and `vxevph`/`1vfqdu`), Software Engineer (lazy `m0001_metadata_v2` import and `MetadataSchemaError` hierarchy), Security/Reliability (fail-closed boolean/int validation and atomic `project.json` replacement), and Modest Executor (one module per `E-*` item with explicit signatures).

### Step R6

- Checked: 5 `E-*` items in 4 task groups across 6 work `- Scope-Paths:` entries (`- Size assessment: standard`), within `nj8zdp` guidance (`<=5` E-items, `<=8` work Scope-Paths, `<=8` units per item; `0` `IPD-Z602`/`IPD-Z603` advisories). No further child-plan split is needed because `g8na48` is already the leaf split out of `vxevph` E-01.

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h` (verified under `.aw/records/plans/executed/`), orchestrator `63ib9r` (`E-56` / Order 101 row), and downstream plans `vxevph` (`executed:g8na48`), `1vfqdu` (`m0001.is_pending`, `write_metadata_schema`, `repo_has_legacy_records`), `cxxmyv`, `x1mmdp`, and `dcerjg` (`V-16` baseline). Confirmed zero sibling plans reference `g8na48` internal `E-*` IDs before splitting `E-03`/`E-05`, and corrected the stale phase-A `1ajqaa` statement in `E-02` (`PR-006`).

### Step S5

- Checked: `OQ-03` (pre-existing resolved non-blocking question, updated with `Recommendation strength: strong.`) and four engineering HOW choices surfaced by `PR-001`..`PR-005`.
- Demonstrated at review via Python probe against `agent_workflows.project_context` at `aca012dc9`: on an unconfigured `TemporaryDirectory`, `resolve_project_context(target_repo=...).logical_roots["records"]` points to `<AW_HOME>/projects/<pid>/records` while `project_config_dir(r) / "project.json"` and `project_records_dir(r)` resolve cleanly to `<tmp>/.aw/config/project.json` and `<tmp>/.aw/records`.
- Recorded all four self-resolved engineering choices in `### Decisions` (`D-1`..`D-4`), all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-05` and `V-01..V-05` per `steps/s6-rereview.md` rule 1 because `E-05` and `V-05` were added via `aw ipd sync --apply`.
- Simplified the `records_root` forwarding contract between `E-01` and `E-02` so `repo_has_legacy_records` always scans `[Path(records_root) if records_root is not None else project_context.project_records_dir(repo), Path(repo) / ".agents"]` and `_require_schema` forwards `records_root=records_root` unconditionally. Verified `5/5` `E-*`/`V-*` bijection, `- Highest E allocated: 05`, and `0` findings from `aw ipd lint --phase author --detail`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / E-01, Step 0 | `agent_workflows/project_context.py:979`, `agent_workflows/project_context.py:1210`, `agent_workflows/artifact_meta.py:1521` | `E-01` resolved roots via `resolve_project_context` (`logical_roots["records"]` defaults to `<AW_HOME>` on unconfigured repos, missing `<repo>/.aw/records` and `<repo>/.agents/` in AC-11 case 1 and C12 shapes (a)-(c)), and detected legacy records only by `- Field:` or `## Workflow history` (missing prose-only `.agents/` records, legacy staged prompts, and multi-key YAML research files). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified `project_config_dir(repo) / "project.json"` (with `config_project` override), `[Path(records_root) if records_root is not None else project_records_dir(repo), Path(repo) / ".agents"]`, and v2 mirror detection via `parse_artifact_mirror`, `parse_review_mirror`, and `parse_staged_prompt_mirror` plus absence of `## Workflow history`. |
| PR-002 | HIGH | IN-SCOPE | R1, R3 / E-01, E-02 | `agent_workflows/artifact_meta.py:3020`, `agent_workflows/artifact_meta.py:3540`, `agent_workflows/meta_cli.py:271` | `E-02` hooked only `check_freshness` (skipping `read_at` and `.agents/` repos where `records_root` does not exist), did not isolate bare `logical_roots`-only `Ctx` test stubs from `os.getcwd()`, and raised an unspecified exception that `meta_cli._collect`'s `except ValueError:` handler would misclassify if derived from `ValueError`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Defined `MetadataSchemaError(RuntimeError)` in `chain.py` and wired `artifact_meta._require_schema` into both `check_freshness` (before `!records_root.exists()`) and `read_at` without falling back to `os.getcwd()` on test stubs. |
| PR-003 | MEDIUM | IN-SCOPE | R1, R3 / E-03, E-05 | `agent_workflows/install_wizard.py:1339`, `agent_workflows/project_schema.py:591` | Adding `"metadata_schema"` to `known_proj_keys` in `install_wizard.persist_project_policy` without extracting `raw_proj.get("metadata_schema")` inside the `except ValueError:` fallback branch silently drops `"metadata_schema"` whenever a sibling key fails `parse_portable_policy`; `parse_portable_policy` also needed explicit non-bool positive-int validation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required non-bool positive-int (`>= 1`) validation in `parse_portable_policy` (`E-03`) and `existing_metadata_schema` preservation in both the `try` and `except ValueError:` branches of `persist_project_policy` (`E-05`, tested in `E-04`/`V-05`). |
| PR-004 | MEDIUM | IN-SCOPE | R2, R7 / E-01, Findings | `.gitignore`, `.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md:39` | `.aw/state/dcerjg/check-before.jsonl` lives under gitignored `.aw/state/` and does not transfer across isolated runner lane worktrees between `g8na48` and `dcerjg` V-16. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `F-03` (verified in `V-01`) so `E-01` records the pre-edit `HEAD` commit SHA and `(location, rule)` pair count in tracked plan text alongside writing `.aw/state/dcerjg/check-before.jsonl`. |
| PR-005 | MEDIUM | IN-SCOPE | R1, R7 / E-01 | `.aw/records/plans/pending/20261107-metastore-15-vxevph-build-the-migration-chain-metadata-schema-stamp-m0001-prefli.ipd.md:7` | `g8na48` creates `chain.MIGRATIONS` holding `m0001`, while `m0001_metadata_v2.py` is created later by `vxevph` (whose `- Scope-Paths:` excludes `chain.py`); an eager import in `chain.py` would fail at import time in `g8na48`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified `m0001.is_pending(repo)` directly over `read_metadata_schema` and `repo_has_legacy_records`, and lazy delegation to `agent_workflows.migrations.m0001_metadata_v2.run` inside `m0001.run`. |
| PR-006 | LOW | IN-SCOPE | R6, Proofreading / E-02..E-05, OQ-03, V-* | `.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md:48`, `:60`, `:114` | `E-02` falsely claimed no CLI command reads through `artifact_meta` yet (`1ajqaa` is already executed), `E-03`/`E-04` carried multi-concern density advisories and an unexplained `(PR-001)` citation, line 114 had two em dashes (`IPD-C802`), `OQ-03` lacked `Recommendation strength:`, and `Proposed changes` lacked a Requirement 12 diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated the `1ajqaa` note, split `E-03`/`E-05` via `aw ipd sync --apply`, clarified `dcerjg` review finding `PR-001`, removed em dashes, added `Recommendation strength: strong.`, and added a Mermaid `flowchart TD` diagram. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `chain.py` resolve `project.json` and candidate record roots across configured, home `clean-delta`, `.agents/`, unconfigured, and `tmp_path` stub repositories? | Resolve `project.json` via `config_project` override or `project_context.project_config_dir(repo) / "project.json"`, and scan `[Path(records_root) if records_root is not None else project_context.project_records_dir(repo), Path(repo) / ".agents"]`. | Call `resolve_project_context.logical_roots["records"]` directly (misses unconfigured `<repo>/.aw/records` and `<repo>/.agents/` because `RecordsBackend.HOME` is the unconfigured default); hard-code `<repo>/.aw/...` (breaks `clean-delta` home/external placement, `4sd62s` 4.5/C12). | `agent_workflows/project_context.py:979`, `agent_workflows/project_context.py:1210`, `4sd62s` C12 | yes |
| D-2 | What exception type should `require_current_schema` raise on an unmigrated repository? | Define and raise `MetadataSchemaError(RuntimeError)` with message containing ``run `aw migrate metadata` ``. | Raise `ValueError` (caught by `meta_cli._collect` at `agent_workflows/meta_cli.py:271` and misclassified as a per-record `invalid-record` defect). | `agent_workflows/meta_cli.py:271`, `4sd62s` 5.3 / AC-11 | yes |
| D-3 | How should `repo_has_legacy_records` distinguish legacy records from v2 records without false positives on synthetic log-only fixtures or v2 `.review.md` files? | Return `True` on any candidate `.md` under `<repo>/.agents/` or any candidate `.md` carrying `## Workflow history` or failing all three `artifact_meta` v2 mirror parsers (`parse_artifact_mirror`, `parse_review_mirror`, `parse_staged_prompt_mirror`), and skip the scan altogether when `stamp >= CURRENT_METADATA_SCHEMA` or `CURRENT_METADATA_SCHEMA <= 1`. | Check only `- Field:` bullets before `##` (misses prose-only `.agents/` records, legacy `<!-- aw-prompt:` files, and multi-key YAML research files); require `meta/<id6>.jsonl` per `.md` file (false-positives on v2 `.review.md` files, which have no log of their own under `4sd62s` 4.1a). | `agent_workflows/artifact_meta.py:1521`, `4sd62s` 4.1, 4.1a, 5.2a, C12 | yes |
| D-4 | How should `chain.MIGRATIONS` wire `m0001` in `g8na48` before `vxevph` creates `m0001_metadata_v2.py`? | Compute `m0001.is_pending(repo)` from `read_metadata_schema` and `repo_has_legacy_records` in `chain.py`, and lazily import `agent_workflows.migrations.m0001_metadata_v2` inside `m0001.run`. | Eagerly import `m0001_metadata_v2` at `chain.py` import time (raises `ModuleNotFoundError` in `g8na48`); leave `MIGRATIONS` empty in `g8na48` (violates `g8na48` E-01 and forces `vxevph` out of its declared `- Scope-Paths:`). | `.aw/records/plans/pending/20261107-metastore-15-vxevph-build-the-migration-chain-metadata-schema-stamp-m0001-prefli.ipd.md:7` | yes |
