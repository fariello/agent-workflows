# Review findings: plan 9vf2iv

- Subject-Id: 9vf2iv
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `7a167f582` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-102-9vf2iv-build-the-five-shape-migration-fixture-corpus-from-a-structu.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` with 0 errors, 0 warnings and 2 `IPD-C802` infos (em dashes in the validation preamble). After edits, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings. The plan adds no code yet. Every measurement below was taken on scratch fixtures under `/tmp/opencode/9vf2iv-probe`, with `AW_HOME` and `HOME` isolated, or on this repository's public git history. No private repository was read.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope, Scope-Paths | Builder only, "derived from a structural survey of the maintainer's repositories" | Builder plus `tests/test_migration_corpus.py`; the evidence is public history plus the `g5hpbb` measurements | PR-003, PR-006. |
| Goal | One builder per shape | Adds a fully committed repository, a caller-given empty directory, a published record set, and `ya4ee4` as a consumer | PR-004, PR-007. |
| E-01 | One paragraph naming five builders and a survey docstring | Per-shape contents tied to consumer needs, `EXPECTED`/`UNCLASSIFIABLE`/`SHAPES`, destination guard, `init_repo`, fixed-date commits, synthetic id6 rule, docstring evidence commands per shape | PR-001..PR-005, PR-007. |
| E-02 (new, `aw ipd sync --apply`) | (absent) | Behavioural test of the builder's own contract, plus refusal tests, schema-proof (no reader assertions) | PR-006. |
| Conventions | Two bullets | Adds the tracked-only sanitizer fact and the `init_repo`/`AW_HOME` isolation convention | PR-002. |
| Findings | F-01..F-03 | Adds F-04..F-10 with review evidence | PR-001..PR-005. |
| Findings (diagram) | (absent) | Mermaid `flowchart TD` of the builder flow and consumers (rendered with `@mermaid-js/mermaid-cli` 12.2.0) | Technical writing standard requirement 12. |
| Deferred | One carrier line | Adds the `home` backend owner (`bv4kkj`), `ya4ee4` E-09, and the attended-survey deferral to OQ-01 | PR-005, PR-007. |
| Scope check, Required tests, Spec sync | `aw find --all`; "shapes found on ONE machine" | `E-02` module, staged sanitizer, history evidence, AC-42 quotation | PR-001, PR-002, PR-003. |
| Open questions | None | OQ-01 (non-blocking, maintainer): an attended survey, with a default | PR-003. |
| Validation preamble | Two em dashes (`IPD-C802`) | Commas | PR-008. |
| V-01, V-02 | `aw find --all`, unrunnable sanitizer target, "the command that produced" private counts | `aw find all --agent --dir`, `inventory_all_artifacts` rows, public-history re-runs, `ValueError` sample, `aw sanitize --agent --staged`, a path grep; V-02 per-check node ids and durations | PR-001, PR-002, PR-006. |
| Approval gate | "All open questions are resolved." | OQ-01 open, non-blocking, with its default | PR-003. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `tests/migration_corpus.py` is a contract consumed by `6oi2nu` E-01/E-03, `3g20ms` V-02, `bv4kkj` E-05, `ya4ee4` E-09 and `g5hpbb` E-07.
2. Yes. The plan governs how evidence from the maintainer's private repositories enters a tracked public file (leak-sanitizer, no names or paths).
3. No. Two `E-*` items after review.
4. No. All `- Scope-Paths:` entries are explicit files.
5. No. Test fixtures only; nothing irreversible.

AW-TIER: complex

### Step R1

- Checked: spec `4sd62s` C12, AC-42, 3c, 5.2a items 1 to 5, 5.3; `aw find --help`, `aw sanitize --help`; `leak_sanitizer._tracked_files`, `_staged_files`; `project_context.project_records_dir`, `_stored_physical_classes`; `status_set.inventory_all_artifacts`, `ArtifactRecord`; `tests.support.init_repo`, `clean_git_env`; `tests/test_records_root_accessor.py::test_accessor_companion`; `record_history` first commit `c3bff2528`; `.aw/.gitignore` `records/history.jsonl`.
- Found PR-001: `aw find --all` is not a valid form (`unrecognized arguments: --all`); the form is `aw find all`, and `--dir` targets a fixture.
- Found PR-002: `aw sanitize --agent tests/migration_corpus.py` exits 2 (`not a git repository`); the sanitizer scans tracked files only, so an untracked module reports clean; a probe showed `--staged` reports `home-path` on the same file.

### Step R2

- Checked: `E-*`/`V-*` bijection (2/2 after `aw ipd sync --apply`); runtime reachability of each `V-*` (V-01 runs the builders and today's readers; V-02 runs the E-02 module); dependency `executed:dcerjg`.
- Found PR-004: "a known set" was undefined, so neither V-01 nor any consumer could check it. Added `EXPECTED`, `UNCLASSIFIABLE` and `SHAPES`, and the exact committed-files outcome.
- Item-Dependencies decision recorded as D-4.

### Step R3

- Checked: the private-data path (survey, docstring, sanitizer), destination safety, git environment inheritance, absolute paths in tracked files.
- Found PR-003: a runner lane cannot read the maintainer's other repositories, and "the command that produced" private survey counts would print private paths into a tracked file and the plan. Evidence now comes from public history (F-04, F-05) and the already-recorded `g5hpbb` F-02/F-03; a fresh survey is OQ-01.
- Found PR-007: "writes only into a directory they are given" had no enforcement. Builders now refuse a relative, non-empty, or inside-a-work-tree destination before writing, use `clean_git_env`, and keep the only absolute path in shape e's untracked `local.json`.

### Step R4

- Checked: determinism (fixed id6 values, fixed commit dates, identical tree ids across builds), committed state, idempotence of consumers' `--apply` (fixtures must start clean), outcome-only tests, `core` budget.
- Found PR-005: the shape contents did not match the consumers' assertions: `bv4kkj` V-02 counts zero `.md` under `.agents/` after apply (so no `.agents/skills`), `bv4kkj` E-05 needs shape d without sidecar-setter history, `3g20ms` V-02 needs the prose plan under `executed/` plus an unclassifiable file, the vxevph preflight refuses uncommitted record changes, and shape e's `home` variant is built by `bv4kkj`. Each is now stated in E-01.

### Step R5

- Checked: QA (V evidence names each unit), testing (the builder had no test of its own), architect (corpus as the shared contract for five plans; reader assertions versus the 5.3 schema gate), novice (where companion config lives, why a module under `tests/` is not collected), stakeholder (AC-42 "from the structure of a real repository").
- Found PR-006: the builder had no behavioural test, and a test asserting `aw find` output would break once `CURRENT_METADATA_SCHEMA` becomes 2 (5.3). Added E-02 testing only git and file bytes; today's-reader agreement is one-time V-01 evidence.

### Step R6

- Checked: 2 `E-*` items, 2 work `- Scope-Paths:` entries; within `nj8zdp` guidance (at most 5 and 8). No split needed.

### Step R7

- Checked: consumers `6oi2nu` (`Item-Dependencies: executed:dcerjg, executed:9vf2iv`), `3g20ms`, `bv4kkj`, `g5hpbb` (`executed:9vf2iv`), `ya4ee4` E-09 (`idless_prose`), orchestrator `63ib9r` child-table row 102 and E-57.
- `ya4ee4` was missing from the Deferred consumers (folded into PR-005). No orchestrator edit is needed: the dependency is unchanged (D-4).

### Step S5

- Checked: evidence source, known-set definition, test-module addition, dependency edge.
- Engineering decisions D-1..D-4 were resolved from repository evidence. One question belongs to the maintainer and is recorded as non-blocking OQ-01 with a default: should a fresh attended structural survey of the private repositories replace or extend the recorded evidence?

### Pass 2

- Re-reviewed E-01, E-02, V-01 and V-02 because E-02 was added via `aw ipd sync --apply` (`steps/s6-rereview.md` rule 1). Tightened shape e determinism (both repositories' tree ids), `AW_HOME` isolation for the `project_records_dir` check, the shape b duplicate-collapse pointer, and the approval-gate sentence. Lint `clean`, 0 findings.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / E-01, V-01 | `aw find --all` -> `agent-workflows: error: unrecognized arguments: --all` | The only reader check named a non-existent flag, so V-01 could not run. | Low | FIXED | `aw find all --agent --dir <root>` plus `status_set.inventory_all_artifacts` rows. |
| PR-002 | HIGH | IN-SCOPE | R1 / V-01, conventions | `leak_sanitizer._tracked_files` (`git ls-files`); probe: untracked `$HOME` path reported `clean`, `--staged` reported `home-path` | The sanitizer check either errors (exit 2) or passes falsely on an untracked module. | Low | FIXED | `aw sanitize --agent --staged` after staging, plus a path grep. |
| PR-003 | HIGH | IN-SCOPE | R3 / E-01, V-01, OQ-01 | Lane prompt (workspace confined to the worktree); V-01 "with the command that produced them" | The survey could not run in a lane, and reproducing it would print private paths. | C:Low; U:Low; S:Low (reduces exposure); F:Med (shape c rests on recorded evidence); overall Low | FIXED | Public-history evidence for shapes a, b, d (F-04, F-05); `g5hpbb` F-03 for c; OQ-01 for an attended survey. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / E-01 | E-01 "lists a known, nonzero set of records" | The known set was undefined, so no one could check it. | Low | FIXED | `EXPECTED`, `UNCLASSIFIABLE`, `SHAPES`; exact committed-files outcome. |
| PR-005 | MEDIUM | IN-SCOPE | R4, R7 / E-01, Deferred | `bv4kkj` V-02 (`find .agents -name '*.md'` zero), `bv4kkj` E-05 (shape d, `home` fixture), `3g20ms` V-02, `ya4ee4` E-09, `vxevph` uncommitted-records refusal | Shape contents did not meet the consumers' assertions. | Low | FIXED | Per-shape contents, all committed, stated in E-01; `ya4ee4` added to Deferred. |
| PR-006 | MEDIUM | UNDER-SCOPE | R5 / E-02, V-02 | spec `4sd62s` 5.3; `g8na48` E-01 `require_current_schema` | The builder had no test of its own, and a reader-based test would break at the cutover. | Low | FIXED | E-02 `tests/test_migration_corpus.py` (`core`) on git and file bytes only; V-02. |
| PR-007 | MEDIUM | IN-SCOPE | R3 / E-01 | Safety section "the builders write only into a directory they are given" | Destination safety was a sentence, not a behaviour. | Low | FIXED | `ValueError` before any write for relative, non-empty, or inside-a-work-tree `dest`; `clean_git_env`; refusal tests. |
| PR-008 | LOW | IN-SCOPE | Proofreading / preamble, Findings | `IPD-C802` x2; no diagram | Em dashes; no diagram for a branching build. | Low | FIXED | Commas; Mermaid flowchart. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the structural evidence come from? | This repository's public history (shapes a, b, d) and recorded `g5hpbb` F-02/F-03 (shape c); shape e from the `project_context` contract | A fresh survey of private repositories in the lane (not permitted; would leak paths) | AC-42 asks for the structure of "a real repository that uses the toolkit"; this repository is one | yes |
| D-2 | How is the known set expressed? | Module constants `EXPECTED`, `UNCLASSIFIABLE`, `SHAPES` | Per-consumer hard-coded expectations | Five consumers would otherwise drift | yes |
| D-3 | Does the builder get its own test? | Yes, `tests/test_migration_corpus.py`, asserting git and file bytes only | Reader assertions (break at 5.3 cutover); no test | `tests/test_repo_template.py` precedent; spec 5.3 | yes |
| D-4 | Keep `- Item-Dependencies: executed:dcerjg`? | Keep | Drop to `none` (the builder uses no `dcerjg` code) | Changing it requires the orchestrator `63ib9r` row 102 to change too, and the consumers all wait on `dcerjg` anyway; no schedule gain | yes |
