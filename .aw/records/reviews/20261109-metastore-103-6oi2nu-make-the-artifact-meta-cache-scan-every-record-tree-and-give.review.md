# Review: 6oi2nu - Make the artifact_meta cache scan every record tree and give id-less records a stable identity

- Subject-Id: 6oi2nu
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

#### Changes
- Replaced the two em dashes (`U+2014`) in the `## Validation and cross-check` reachability sentence with commas (`IPD-C802`).
- Expanded the one-line `## Proposed changes` entries so each names the module and symbol it changes, and added a Requirement 12(b) `mermaid` `flowchart TD` of the scan, the stored-path form and the identity choice, with one sentence on why `E-04` runs first.
- Rewrote `## Findings` so each row cites a symbol or quoted string and the evidence header carries the measurement dates and commit (`83f29302f`).
- Changed OQ-01 `- Owner: none` to `- Owner: plan author`.
- Added a `## Behavior decisions` section (`D-1` to `D-5`).

#### Issues
- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`. Recommendation strength for the remaining prose: strong.

### Step T

1. Yes. The plan changes the cache path contract (spec `4sd62s` 4.5a says every cache `path` is records-root-relative and never outside the root) and the identity form of id-less records, which the reader-move plans (`cdglt1`, `r81uvz`, `ffceq0`) and `3g20ms` rely on; after revision it amends spec `4sd62s`.
2. No. It touches no leak, commit, worktree, merge, or sandbox code.
3. Moderate. 6 `E-*` items after revision in two task groups, in `agent_workflows/artifact_meta.py`, `agent_workflows/meta_cli.py`, one spec and one new test module.
4. Yes. 4 work `Scope-Paths` plus the plan file after revision; the original fence missed `agent_workflows/meta_cli.py` (it calls `check_freshness` and resolves path selectors) and the spec file.
5. High. Every `artifact_meta` read (`read`, `history`, `resolve`, `query`, `append`) keys on the id6 and joins the stored path, so a wrong path form or identity breaks reads in every repository. The cache is gitignored and rebuildable, so recovery is a rebuild, but the spec contract is shared.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/artifact_meta.py` (`load_legacy_artifact`, `check_freshness`, `_load_sources`, `read`, `history`, `resolve`, `query`, `review_rows`, `append`, `create`, `repair`, `open_cache`, `compute_schema_hash`, `LEGACY_LOADER_VERSION`, `LegacyTarget.key`, `legacy_context`, `validate_id6`, `_check_path_safety`, `SUPPORTED_TYPES`, `_LEGACY_PLURAL_TO_TYPE`, `_LEGACY_MINT_POOLS`), `agent_workflows/artifact_core.py` (`ID6_ALPHABET`, `ID6_RE`, `generate_id6`, `global_id6s`, `mint_id6`), `agent_workflows/selectors.py` (`record_dirs`, `_record_dirs_cached`, `_OTHER_SWEEP_SKIP_DIRS`, `_SKIP_NAMES`), `agent_workflows/status_set.py` (`inventory_all_artifacts`, `detect_artifact_type`, `read_artifact_record`), `agent_workflows/meta_cli.py` (`MetaContext`, `meta_context`, `resolve_selector`, `index_rebuild`, `refresh_cache`), `agent_workflows/project_context.py` (`ProjectContext.target_repo`, `record_git_root`), spec `4sd62s` C12, 5.2a, 4.5a ER and step 3a, and the `9vf2iv`, `g5hpbb`, `3g20ms` and `ffceq0` plans.
- `E-02` offered "a reserved, non-mintable prefix" for the derived identity. `artifact_core.generate_id6` draws every position from the full base36 alphabet, so no six-character prefix is reserved, and any non-id6 form fails `validate_id6` in six functions and `artifacts.id6 TEXT PRIMARY KEY`. A deterministic id6 with a collision walk was demonstrated in two processes (`0uf2yo` both times; `2xaht4` when `0uf2yo` was taken) and is now `D-3` (`PR-001`).
- `E-01` gave no stored-path form for a `.agents/` file: `load_legacy_artifact` raises `ValueError ... is not in the subpath of` on `path.relative_to(records_root)`, and eight sites join `records_root / <stored path>`. The `@repo/` form was demonstrated to round-trip in a scratch repository where the records root does not exist, and it is now `D-1` with helpers in the new `E-04` and a spec amendment in the new `E-05` (`PR-002`).
- `E-01` said record_dirs covers ".agents/docs/<type>". It adds only `.agents/docs/research`; `.agents/docs/specs` and `.agents/workflows` arrive through the `other` sweep (scratch: `specs` gave none, `other` gave `.agents/workflows`, `.agents/docs`). Typing therefore follows `detect_artifact_type`, not the directory that found the file (`PR-004`).
- `E-02` claimed instability only "on every cold cache build"; a scratch id-less spec also changed id6 after a one-line edit (`8i63bk`, `8i63bk`, `efguhv`, `kmkq94`). The four-build check now covers it (`PR-008`).

### Step R2

- Checked: the `E-*`/`V-*` bijection (`E-01`..`E-06` <-> `V-01`..`V-06`), `- Scope-Paths:` completeness against every changed symbol, `- Item-Dependencies:` (`dcerjg`, `9vf2iv`; `g5hpbb` and `3g20ms` depend on this plan), the pin-first rule, and `aw ipd lint --phase review-finalize --agent`.
- `E-01` did not say how the scan learns the repository root: `legacy_context` and `meta_cli.MetaContext` carry `repo_root`, `ProjectContext` carries `target_repo`, and the test contexts carry only `logical_roots`. `check_freshness` also returns early when the records root does not exist, which is exactly shape (a). Added `_scan_repo_root` (`E-04`), the extra-roots-only walk (`E-01`) and the caller wiring including `meta_cli` (new `E-06`); `agent_workflows/meta_cli.py` added to `- Scope-Paths:` (`PR-005`).
- Existing caches would never rebuild: `open_cache` rebuilds only when `compute_schema_hash` changes, which folds in `LEGACY_LOADER_VERSION` (`"legacy_v3"`). `E-01` now bumps it to `"legacy_v4"` (`PR-006`).
- `V-01` demanded "the record-parity probe of backlog `suth7l`" output `records_disagreeing: 242`. That probe exists only as prose in the backlog item, and the same comparison measured today reports 246 Set differences (242 plus 4 legacy-timestamp plans). `V-01` now carries an inline probe and demands an empty before/after `diff`, with today's numbers stated (`PR-007`).
- Pin-first wrote to `.aw/state/g5hpbb/` and named no test command. It now writes to `.aw/state/6oi2nu/` with the `s95hj6` command over the seven baseline modules (`100 passed in 8.39s` at `83f29302f`) (`PR-009`).
- Added stop conditions for absent `9vf2iv` builders or changed `artifact_meta`/`selectors` symbols, and for an unmergeable concurrent edit (`PR-011`).

### Step R3

- Checked: `_check_path_safety` (refuses `..` and absolute event paths), the `@repo/` form against it (cache-only; never an event path, because a derived record is written by path through `LegacyTarget`), and the write path of a derived id6.
- A derived id6 written into a file or the sidecar would mint a real-looking id outside the migration, which OQ-01 forbids. `E-02` now builds `LegacyTarget(<file>, <plural>, None)` for a derived id6, so `LegacyTarget.key` keys the write by path, and `E-03` case (f) proves no id6 reaches the file or `records/history.jsonl` (`PR-003`).
- No secret, network or privileged path is involved; the scan reads only directories `selectors.record_dirs` already returns.

### Step R4

- Checked: in-root behavior preservation (no in-root stored path changes; extra-root skips apply only to extra-root files, `D-4`), the parity numbers on this repository (3391 cache rows, 3355 inventory records, 0 missing, 0 declared-id6 mismatches, 0 status mismatches, 246 Set mismatches), cost (`query` 0.89 s to 0.93 s per process; extra-root computation 0.035 s), and the `other` sweep's toolkit docs (`D-5`).
- `E-01`'s "every record in the before-dump" counted records `inventory_all_artifacts` finds through the `other` sweep and `roadmaps`, which the cache types by `type_map` with default `ipd`. `D-2` keeps that typing rule for both trees and names it (`PR-004`).
- `E-03` gave no tier marker, fixture source or slow-test rule. It now sets `pytestmark = pytest.mark.core`, uses the `9vf2iv` builders, marks a test over 2 s `slow` instead of editing `tests/slow_allowlist.txt` (outside the fence), and adds the read, history, context-form, collision and no-write cases (`PR-010`).

### Step R5

- Checked: the eight reviewer personas (QA/QC, testing and regression, UI/UX, architect, software engineer, power user, novice, stakeholder).
- QA and testing: the four-build identity check and the before/after `diff` catch the two regressions most likely here (unstable id, in-root drift).
- Architect: the `@repo/` form keeps every in-root path and the spec contract intact for the shapes that already work, and is confined to phase B (`D-1`, `E-05`).
- Power user: a derived id6 shown by `aw show` stops resolving after the migration mints the permanent one; this is recorded in `D-3` and is strictly better than today, where it stops resolving on the next edit.
- Stakeholder: C12 requires the phase-A cache to serve shapes (a), (b) and (e) before any reader move merges (spec step 3a); this plan delivers that.

### Step R6

- Checked: whether the plan should become its own Set.
- No split. Six E-items is one over the advisory guidance (`IPD-Z603`, info). `E-04`, `E-01`, `E-06` and `E-02` change one scan in one module and have no green intermediate merge (stored paths need the helpers; the scan needs its callers); `E-05` is the spec note of the same change and `E-03` its tests. Recorded as the gate's cohesion rationale.

### Step R7

- Checked: `g5hpbb` (parent; F-01, F-05, OQ-01, E-07), `9vf2iv` (builders), `3g20ms` (mints the permanent id6 via `artifact_core.mint_id6`; depends on this plan), `bv4kkj` (layout stage), `ffceq0` (`## Scope check` allows `E-12` to extend the legacy loader's scan roots to `.agents/`), `cdglt1`, `r81uvz`.
- `ffceq0` overlaps `E-01` on the `.agents/` scan. This plan now owns it, and the Deferred section names `ffceq0` as the carrier for consuming `id_derived` and `source_path` in its parity test. The ordering holds: `ffceq0` depends on `g5hpbb`, which depends on this plan (`PR-012`).
- `3g20ms` E-02 mints through `artifact_core.mint_id6`, whose collision set comes from files, not the cache, so a derived id6 never blocks or shadows a minted one.

### Step S5

- All twelve findings are fixed in place with `Low` or `Medium` remediation risk. Every decision (`DEC-001`..`DEC-005`) is answered from repository code, spec `4sd62s` and demonstrations run in this review. All are reversible: the cache is gitignored and rebuilds on the loader-version bump, and the spec notes are phase-B only. OQ-01 stays resolved. The spec amendment of `E-05` is surfaced to the maintainer as a non-blocking notice in the runner outcome, because it edits an approved contract.

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-103-6oi2nu-make-the-artifact-meta-cache-scan-every-record-tree-and-give.ipd.md` top to bottom after the revisions.
- Swept superseded wording: no remaining "reserved, non-mintable prefix", "path_key", ".agents/docs/<type>", `.aw/state/g5hpbb/`, `records_disagreeing: 242` or "cold cache build" only claim. `## Scope`, `## Proposed changes`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync` and the gate match `E-01`..`E-06` and `D-1`..`D-5`; `- Highest E allocated:` reads `06`.
- `aw ipd lint --phase review-finalize --agent`: `outcome: clean`, 0 errors, 0 warnings, 1 info (`IPD-Z603`, six E-items). Zero em or en dashes. `aw sanitize --agent`: `outcome: clean`, `findings: 0`.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 | `agent_workflows/artifact_core.py::generate_id6` (every position from `ID6_ALPHABET`); `ID6_RE` `\A[0-9a-z]{6}\Z`; `artifact_meta.validate_id6` in `load_legacy_artifact`, `read`, `history`, `read_at`, `create`, `append` | `E-02`'s "reserved, non-mintable prefix" cannot exist, and a `path_key` alternative would need a second identity at every `validate_id6` site | Low | FIXED | `D-3`: a derived id6 from `sha256(stored_path + "\0" + k)` with a collision walk against the mint pool and declared ids, plus an `id_derived` marker; demonstrated stable in two processes |
| PR-002 | BLOCKER | UNDER-SCOPE | R1 / spec | `artifact_meta.load_legacy_artifact` (`path.relative_to(records_root)` raises for a `.agents/` file); `records_root / <stored path>` joins in `_load_sources`, `history`, `append`, `repair`; spec `4sd62s` 4.5a ("never outside the root") | No stored-path form for extra-root files, so `E-01` would crash the loader or contradict the spec | Medium | FIXED | `D-1` `@repo/` form, `stored_path`/`source_path` helpers in new `E-04`, demonstrated round-trip; spec note in new `E-05`; spec added to `- Scope-Paths:` and the spec-sync section |
| PR-003 | HIGH | UNDER-SCOPE | R3 | `artifact_meta.append` (`LegacyTarget(records_root / rel, plural, target)` with the id6 string); `LegacyTarget.key`; OQ-01 | A derived id6 passed to `append` could be written to a file or the sidecar, minting outside the migration | Low | FIXED | `E-02` builds `LegacyTarget(<file>, <plural>, None)` for a derived id6; `E-03` case (f) and `V-02` prove nothing is written |
| PR-004 | HIGH | IN-SCOPE | R1 / R4 | `selectors._record_dirs_cached` (adds only `.agents/docs/research`; `other` sweep returns `.agents/docs`, `.agents/workflows`); `load_legacy_artifact` `type_map.get(top_dir, "ipd")` | `E-01` misstated the `.agents/docs/<type>` coverage and named no typing rule for extra-root and `other`-sweep files | Low | FIXED | `E-01` lists the extra roots the sweep yields; `D-2` types by `status_set.detect_artifact_type` and keeps the `ipd` default; `D-4`, `D-5` name the skips and toolkit docs |
| PR-005 | HIGH | UNDER-SCOPE | R2 | `artifact_meta.check_freshness` (`if not records_root.exists(): return`); `legacy_context.repo_root`, `ProjectContext.target_repo`, test contexts with only `logical_roots`; `meta_cli.index_rebuild`, `refresh_cache` call `check_freshness` | No way to learn the repository root, an early return for shape (a), and `meta_cli` callers outside the fence | Low | FIXED | `_scan_repo_root` (`E-04`), extra-roots-only walk (`E-01`), new `E-06` wiring the readers and `meta_cli`; `agent_workflows/meta_cli.py` added to `- Scope-Paths:` |
| PR-006 | HIGH | UNDER-SCOPE | R2 | `artifact_meta.compute_schema_hash` (folds `LEGACY_LOADER_VERSION`); `open_cache` rebuild test; `LEGACY_LOADER_VERSION = "legacy_v3"` | Existing caches would never rebuild, so the new scan and identity would not apply | Low | FIXED | `E-01` bumps to `"legacy_v4"`; `V-01` demands the diff line |
| PR-007 | HIGH | IN-SCOPE | R2 | backlog `suth7l` Evidence (prose numbers only, no script); measured 2026-11-14: 246 Set mismatches, not 242 | `V-01`'s parity probe was not reproducible and its hardcoded count is already wrong | Low | FIXED | Inline probe in `V-01`, saved before and after under `.aw/state/6oi2nu/`, with an empty `diff` and today's numbers stated |
| PR-008 | MEDIUM | IN-SCOPE | R1 | Scratch id-less spec: `8i63bk` cold, `8i63bk` warm, `efguhv` after an edit, `kmkq94` after deleting `index.db` | `E-02` claimed instability only on cold builds; an edit also changes the id6 | Low | FIXED | `E-02`, `E-03` (b) and `V-02` check cold, warm, after-edit and deleted-cache builds |
| PR-009 | MEDIUM | IN-SCOPE | R2 | Original `E-01` (`.aw/state/g5hpbb/<shape>-before.json`); `s95hj6` PIN-FIRST rule | Pin-first wrote into another plan's state dir and gave no test command | Low | FIXED | PIN-FIRST rule writes to `.aw/state/6oi2nu/` with the `s95hj6` command over the seven baseline modules |
| PR-010 | MEDIUM | UNDER-SCOPE | R4 | `tests/test_artifact_meta_loader_parity.py` (`pytestmark = pytest.mark.core`); `conftest.py` slow warning; `tests/slow_allowlist.txt` outside `- Scope-Paths:` | `E-03` named no tier marker, fixture source or slow-test rule, and lacked read, history, context-form and collision cases | Low | FIXED | `E-03` cases (a) to (f), `pytest.mark.core`, `9vf2iv` builders, `slow` marker instead of an allowlist edit; `V-03` updated |
| PR-011 | LOW | IN-SCOPE | Proofreading / gate | `## Validation and cross-check` (two `U+2014`); OQ-01 `- Owner: none`; one-line `## Proposed changes`; gate without stop conditions; `3g20ms` gate (safety stop) | Two `IPD-C802` em dashes, no diagram, no Behavior decisions section, no stop condition for absent prerequisites | Low | FIXED | Dashes replaced, owner set, mermaid diagram and `## Behavior decisions` added, STOP CONDITIONS added and cited in the gate |
| PR-012 | LOW | IN-SCOPE | R7 | `ffceq0` `## Scope check` ("`artifact_meta.py` changes only if E-12 must extend the legacy loader's scan roots to the `.agents/` record root") | Two plans could both own the `.agents/` scan | Low | FIXED | This plan owns the scan; the Deferred section names `ffceq0` as the consumer of `id_derived` and `source_path`; ordering holds through `g5hpbb` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| DEC-001 | How is an extra-root file's path stored in the cache? | `@repo/<repository-relative POSIX path>`, mapped back by `source_path`; in-root paths unchanged (`D-1`) | Repository-relative paths for all records; `../` relative paths | `artifact_meta._check_path_safety` (refuses `..`); spec `4sd62s` 4.5a path notes; scratch round-trip demonstration 2026-11-14 | yes |
| DEC-002 | What is an id-less record's phase-B identity? | Derived id6 from `sha256(stored_path + "\0" + k)` with a collision walk and an `id_derived` marker (`D-3`) | Reserved prefix; separate `path_key` column; keep random mint | `artifact_core.generate_id6`, `ID6_RE`, `validate_id6` sites; two-process demonstration (`0uf2yo`, collision `2xaht4`) | yes |
| DEC-003 | How is an extra-root file typed? | `status_set.detect_artifact_type` mapped through `_LEGACY_PLURAL_TO_TYPE`, facet overrides, default `ipd` (`D-2`) | Type by the directory that found it; refuse untyped files | `selectors._record_dirs_cached` `other` sweep; in-root `type_map` default `ipd` (8 `comms`, 5 `prompt-library`, 1 `roadmaps` rows) | yes |
| DEC-004 | Do extra-root skips also change in-root caching of `README.md` and companion files? | No; skips apply to extra-root files only (`D-4`) | Apply `_SKIP_NAMES` to the in-root walk too | Measured 26 `README.md` and 3 companion rows in the in-root cache; goal of no in-root drift | yes |
| DEC-005 | Does the plan amend spec `4sd62s`? | Yes, two phase-B notes in 5.2a item 3 and the 4.5a `ARTIFACTS` diagram (`E-05`), declared in `- Scope-Paths:` | Leave the spec unchanged and contradict it; block on the maintainer | AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"; spec 4.5a "never outside the root"; maintainer told via the runner outcome `questions[]` 2026-11-14 | yes |
