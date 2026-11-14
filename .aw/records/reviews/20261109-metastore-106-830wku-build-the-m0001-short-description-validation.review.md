# Review findings: plan 830wku

- Subject-Id: 830wku
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-4-carbon
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `e3470de08` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-106-830wku-build-the-m0001-short-description-validation.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 errors, 0 warnings, 2 `IPD-C802` info advisories for the two em dashes in the validation preamble). The baseline modules passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_artifact_meta_write.py tests/test_leak_sanitizer.py tests/test_leak_sanitizer_machine_flags.py` printed `33 passed in 7.99s` and `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_artifact_meta_registry.py` printed `21 passed in 0.36s`. After revisions, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope | Named only `validate(text, repo)` and said "creating the module if `odeo9z` has not yet" | Names `normalize_description`, `build_describe_ruleset`, and `validate(text, repo, *, ruleset=None)` created ahead of `odeo9z` | PR-001, PR-002, PR-003 |
| E-01 | Accepted empty/blank strings, stripped quotes/whitespace internally without exposing normalized text, called `build_ruleset` without `ruleset` or `2xwb9b` D-02 filter, and checked bare `token.startswith("/")` | Exports `normalize_description` and `build_describe_ruleset` (`artifact_meta._writer_ruleset`), refuses empty normalized text, strips surrounding sentence punctuation before checking `>=2`-segment POSIX or Windows drive paths, and tests CI-portable synthesized/monkeypatched leak cases | PR-001, PR-002, PR-003 |
| Project conventions | Did not note `refuse_unsafe_descriptive("") == None`, `_writer_ruleset` (`2xwb9b` D-02), `g8na48` `migrations/__init__.py`, or `leak_sanitizer._ALLOWED_PATHS` | Records all four conventions and `_GENERIC_DERIVED_TOKENS` portability | PR-001, PR-002, PR-003 |
| Findings | F-01 listed three helpers; no F-03 on caller normalization or ruleset parity | F-01 adds `artifact_meta._writer_ruleset` and `_check_no_absolute_paths_in_text`; F-03 documents `normalize_description`, `build_describe_ruleset`, and the `odeo9z` E-06 caller note | PR-001, PR-002 |
| Proposed changes | Six-word fragment (`1. E-01: validate and its tests.`), no diagram | Complete imperative sentence plus a Mermaid `flowchart TD` of the five-stage validation pipeline | PR-004 (Requirement 12) |
| Required tests, Validation V-01 | Six refusal cases using ambient host/home only, two em dashes (`IPD-C802`), no `aw sanitize` or bare core gate | Replaces em dashes with commas; covers empty/blank/`'""'`, punctuation-wrapped absolute paths, synthesized/monkeypatched `home-path` and `derived:<host>`, `normalize_description`, `ruleset` reuse, `test_artifact_meta_registry.py`, `aw sanitize --agent`, and bare `python3 -m pytest` | PR-001, PR-002, PR-003, PR-004 |
| Approval and execution gate | No prerequisite stop; `Honesty rule` named no specific commands | Adds narrow unsafe-condition stop for absent `migrations/__init__.py` or `_writer_ruleset`, forbids `/home/<non-placeholder>` literals in test source, and names all required validation commands | PR-002, PR-003 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Defines the public `m0001_describe` validation interface (`normalize_description`, `build_describe_ruleset`, `validate`) and creates `tests/test_m0001_describe.py`, both relied on by `odeo9z` and `ya4ee4`.
2. Yes. Implements the OQ-31 trust-boundary sanitizer guarding model-generated descriptions against leaking local paths, usernames, hostnames, and session IDs into permanent tracked logs.
3. No. One execution item (`E-01`) in one task group across one production module and one test module.
4. Yes. `- Scope-Paths:` lists `agent_workflows/migrations/m0001_describe.py`, `tests/test_m0001_describe.py`, and the plan file (`agent_workflows/migrations/__init__.py` is created upstream by `g8na48` E-01 via `dcerjg`).
5. Yes. A validation bypass leaks personal machine identifiers into ~3,100 tracked `meta/*.jsonl` logs at cutover, while stripping quotes only inside `validate` causes `odeo9z` to journal unstripped strings that `artifact_meta` later refuses.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Section 4.2 SHORT DESCRIPTION and SAFEGUARDS lines 715-755, AC-36 lines 297-315, OQ-31 lines 2370-2380); `agent_workflows/artifact_meta.py` (`_check_string_safety`, `_check_no_absolute_paths_in_text`, `_check_leak_sanitizer`, `_writer_ruleset`, `validate_new_events` lines 658-874); `agent_workflows/attention_contract.py` (`_is_safe_descriptive_bounded`, `refuse_unsafe_descriptive` lines 684-780); `agent_workflows/leak_sanitizer.py` (`_FAIL_PATTERNS`, `_ALLOWED_LINE_SUBSTRINGS`, `_ALLOWED_PATHS`, `_GENERIC_DERIVED_TOKENS`, `derive_warn_tokens`, `build_ruleset`, `scan_text` lines 72-164, 469-680); `agent_workflows/home_path_patterns.py` (`HOME_PATH_RULES` lines 20-36); `tests/test_artifact_meta_registry.py`, `tests/test_artifact_meta_write.py`, `tests/test_leak_sanitizer.py`, `tests/test_leak_sanitizer_machine_flags.py`.
- `attention_contract.refuse_unsafe_descriptive` returns `None` on `""` and `leak_sanitizer.scan_text` returns `[]` on `""`, so an empty or `""`-quoted reply was not refused by any cited helper (PR-001).
- `artifact_meta.validate_new_events` scans with `artifact_meta._writer_ruleset(repo_root)` (added by executed plan `2xwb9b` D-02 to exclude `.aw/worktrees/<lane>` sibling lane directory names from `warn` rules), not raw `leak_sanitizer.build_ruleset(repo, include_warn=True)` (PR-002).

### Step R2

- Checked: 1:1 `E-01`/`V-01` bijection, `- Scope-Paths:` completeness, `- Item-Dependencies: executed:dcerjg` (`dcerjg` transitively requires `vxevph` and `g8na48`, which creates `agent_workflows/migrations/__init__.py`), and reachability and portability of every `V-01` check.
- `odeo9z` declares `- Item-Dependencies: executed:dcerjg, executed:830wku`, so `830wku` always executes before `odeo9z` and creates `agent_workflows/migrations/m0001_describe.py` and `tests/test_m0001_describe.py` rather than conditionally extending `odeo9z` (PR-003).
- `tests/test_m0001_describe.py` is not in `leak_sanitizer._ALLOWED_PATHS`, and CI containers often use `/root` or `_GENERIC_DERIVED_TOKENS` hostnames (`runner`, `ubuntu`), so `E-01`/`V-01` now specify runtime-synthesized / monkeypatched `home-path` and `derived:<host>` fixtures plus `aw sanitize --agent` verification (PR-002, PR-003).

### Step R3

- Checked: OQ-31 trust-boundary threat model (untrusted record prose fed to an external model whose reply becomes tracked public metadata).
- Verified that `validate` enforces default-deny across all four layers: non-empty normalized text, single-line `<= 300` control-character-free descriptive text, `leak_sanitizer.scan_text(..., include_warn=True)` (`fail` and `warn` findings), and multi-segment POSIX / Windows drive paths even when wrapped in sentence punctuation, quotes, backticks, or parentheses (`("/home/alice/x").`, `` `/opt/app/key` ``), while keeping `/plan-review` and relative repo paths allowed (PR-001, PR-002).

### Step R4

- Checked: caller/callee data flow with `odeo9z` `E-06`, subprocess overhead of `leak_sanitizer.build_ruleset` (`git config --get` calls in `derive_warn_tokens`), quote-normalization edge cases (matching vs unmatched quotes, inner text preservation), and conceptual density (`IPD-Z603` clean, 0 advisories).
- Exporting `normalize_description(text) -> str` alongside `validate(text, repo, *, ruleset=None) -> str \| None` lets callers journal the exact normalized string that passed validation while keeping `validate(text, repo)` backward-compatible with `odeo9z` (PR-001).
- Accepting optional `ruleset` built via `build_describe_ruleset(repo)` (`artifact_meta._writer_ruleset`) satisfies `E-01`'s "built once per run" requirement without spawning ~6,200 `git config` subprocesses across ~3,100 records or polluting multi-repo unit tests with a global cache (PR-002).

### Step R5

- Checked: eight reviewer personas from `.aw/system/workflows/release-review/00-run-protocol.md` (QA/QC, Testing and regression, UI/UX, Architect, Software engineer, Power user, Novice, Stakeholder).
- QA/QC and Software engineer viewpoints surfaced the `'""'` empty-quote pass-through and immutable-`str` normalization loss (PR-001), as well as punctuation-wrapped absolute paths in prose sentences (PR-002).
- Testing/regression surfaced CI container hostname/home variability (`_GENERIC_DERIVED_TOKENS`) and `aw sanitize` self-cleanliness on `tests/test_m0001_describe.py` (PR-002, PR-003). Architect and Stakeholder viewpoints confirmed alignment with `4sd62s` 4.2 SAFEGUARDS, OQ-31, and AC-36.

### Step R6

- Checked: plan size and cohesion (`1` `E-*` item, `2` work paths in `- Scope-Paths:`, zero `IPD-Z603` advisories).
- `830wku` is already a single-module, single-concern leaf split from `odeo9z` `E-05`. No further split is warranted.

### Step R7

- Checked: Order-00 orchestrator `63ib9r` (`E-20` `odeo9z` depends on `E-04` `dcerjg` and `E-61` `830wku`), upstream prerequisites `tve77h`, `2xwb9b`, `g8na48`, `vxevph`, and `dcerjg`, and downstream consumers `odeo9z` (`E-06` `describe_record`) and `ya4ee4` (`E-07`, `E-09`).
- Confirmed `-k validate` test selection in `830wku` `V-01` is disjoint from `odeo9z`'s `-k prompt`, `-k journal`, `-k "argv or env or agy"`, `-k "generate or scratch or spawn_refused"`, and `-k "regenerate or describe_record"` selectors, and noted in `F-03` that `odeo9z` `E-06` should store `normalize_description(reply)` and pass `build_describe_ruleset(repo)`.

### Step S5

- Checked: no pre-existing open questions; all four engineering decisions (`D-1..D-4`) were resolved from authoritative spec, code, and sibling-plan evidence (`Reversible: yes`). Zero unfixed findings and zero human-owned questions remain.

### Pass 2

- Re-read all 126 lines of revised `830wku` after editing `Scope`, `E-01`, `Project conventions`, `Findings`, `Proposed changes`, `Required tests`, `V-01`, and `Approval and execution gate`. Tightened `V-01`'s no-source-inspection `rg` check (`^(import|from) (inspect|ast)\b|\.read_text\(`) so relative-path test strings in `tests/test_m0001_describe.py` do not false-positive. Verified zero em/en dashes and `aw ipd lint --phase review-finalize --agent` (`clean`, 0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | R4-A / R7 | `.aw/records/plans/pending/20261109-metastore-106-830wku-build-the-m0001-short-description-validation.ipd.md:40-42`; `agent_workflows/attention_contract.py:684-693,752-780`; `agent_workflows/leak_sanitizer.py:629-630`; `.aw/records/plans/pending/20261107-metastore-20-odeo9z-build-the-m0001-description-journal-tool-less-model-call-and.ipd.md:64-66` | Two defects in `E-01`: (1) `attention_contract.refuse_unsafe_descriptive` returns `None` on `""` and `leak_sanitizer.scan_text` returns `[]` on `""`, so empty, whitespace-only, or empty-quoted replies (`""`, `"   "`, `'""'`, `"''"`) pass `validate` as `None` and let `odeo9z` `E-06` journal blank descriptions; (2) stripping surrounding whitespace and quotes inside `validate(text, repo) -> str \| None` without exposing a normalizer leaves `odeo9z` `E-06` journaling unstripped raw replies (such as 302-char quoted strings or trailing `\n`) that `artifact_meta.validate_new_events` refuses at cutover. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `normalize_description(text) -> str`, made `validate` normalize first and refuse empty/blank text, pinned empty/quoted/unmatched-quote cases in `E-01`/`V-01`, and noted `normalize_description` usage for `odeo9z` `E-06` in `F-03` (very strong). |
| PR-002 | HIGH | IN-SCOPE | R1 / R3 / R4-A / R7 | `.aw/records/plans/pending/20261109-metastore-106-830wku-build-the-m0001-short-description-validation.ipd.md:40-42,105`; `agent_workflows/artifact_meta.py:701-712,754-773`; `agent_workflows/leak_sanitizer.py:120-146,478-540,547-601`; `agent_workflows/home_path_patterns.py:20-36` | Three mismatches in `E-01` and `V-01`: (1) calling `leak_sanitizer.build_ruleset(repo, include_warn=True)` inside 2-arg `validate(text, repo)` spawns two `git config` subprocesses per call and omits `artifact_meta._writer_ruleset`'s `2xwb9b` D-02 filter excluding `.aw/worktrees/<lane>` sibling directory warn tokens; (2) prose sentences wrapping an absolute path in quotes, parentheses, or backticks (`("/home/alice/x").`) bypass bare `token.startswith("/")`; (3) ambient `Path.home()` / `socket.gethostname()` do not trigger `home-path` or `derived:<host>` in `/root` or `_GENERIC_DERIVED_TOKENS` CI containers, while literal `/home/<user>` strings in `tests/test_m0001_describe.py` fail `aw sanitize`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `build_describe_ruleset(repo)` delegating to `artifact_meta._writer_ruleset(Path(repo))` and optional `ruleset` on `validate`, stripped wrapper punctuation from tokens before the POSIX/Windows path check, and specified runtime-synthesized/monkeypatched leak fixtures in `E-01`/`V-01` (very strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R7 | `.aw/records/plans/pending/20261109-metastore-106-830wku-build-the-m0001-short-description-validation.ipd.md:6,40,105,118-122`; `.aw/records/plans/pending/20261107-metastore-20-odeo9z-build-the-m0001-description-journal-tool-less-model-call-and.ipd.md:8`; `.aw/records/plans/pending/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md:43` | `Scope` and `E-01` said "creating the module if `odeo9z` has not yet" even though `odeo9z` depends on `executed:830wku`; `Approval and execution gate` lacked a narrow unsafe-condition stop for absent `agent_workflows/migrations/__init__.py` (`dcerjg`/`g8na48`) or `_writer_ruleset`; and `V-01` / `Honesty rule` omitted `aw sanitize --agent`, `tests/test_artifact_meta_registry.py`, and bare `python3 -m pytest`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Stated explicitly that `830wku` creates `m0001_describe.py` and `tests/test_m0001_describe.py` before `odeo9z`, added the narrow unsafe-condition stop, and required `test_artifact_meta_registry.py`, `aw sanitize --agent`, and bare `python3 -m pytest` in `V-01` and `Honesty rule` (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261109-metastore-106-830wku-build-the-m0001-short-description-validation.ipd.md:60-76,102`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` was a six-word fragment with no Mermaid `flowchart TD` diagram for the five-stage branching validation pipeline (Requirement 12b), and the `Validation and cross-check` preamble contained two em dashes (`IPD-C802`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Proposed changes` as a complete sentence with a `flowchart TD` diagram and replaced both em dashes with commas (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `m0001_describe` expose quote/whitespace stripping without breaking `odeo9z`'s `validate(text, repo) -> str \| None` signature? | Export `normalize_description(text) -> str` alongside `validate(text, repo, *, ruleset=None) -> str \| None` (which normalizes first and refuses empty/blank strings) | Change `validate` to return `(cleaned, reason)` (breaks `odeo9z` E-06 signature); strip only inside `validate` (leaves `odeo9z` journaling unstripped strings that `artifact_meta` refuses) | `odeo9z` E-06 and Deferred (`odeo9z:64,95`); `agent_workflows/attention_contract.py:684-693`; `agent_workflows/artifact_meta.py:868-873` | yes |
| D-2 | How should `validate` construct and reuse the leak-sanitizer ruleset across a migration run? | Provide `build_describe_ruleset(repo)` delegating to `artifact_meta._writer_ruleset(Path(repo))` (`2xwb9b` D-02) and optional `ruleset=None` on `validate` | Rebuild `leak_sanitizer.build_ruleset` on every `validate` call (spawns two `git config` subprocesses per call and falsely flags `.aw/worktrees/<lane>` sibling names); cache globally ignoring `repo` (breaks multi-fixture tests) | `agent_workflows/artifact_meta.py:754-773`; `agent_workflows/leak_sanitizer.py:491-501,547` | yes |
| D-3 | How should the absolute-path check treat sentence punctuation around path tokens? | Strip leading `` `"'([{< `` and trailing `` `"'.,;:!?)]}> `` from each whitespace token before testing Windows drive or `>=2`-slash POSIX `/path` | Bare `token.startswith("/")` (misses `("/home/alice/x").` and `` `/opt/app/key` ``); unanchored substring regex (falsely flags relative repo paths and `https://` URLs) | `agent_workflows/artifact_meta.py:658,701-712`; `agent_workflows/home_path_patterns.py:20-36` | yes |
| D-4 | How should `tests/test_m0001_describe.py` test `home-path` and `derived:<host>` deterministically across CI containers while passing `aw sanitize`? | Synthesize leak tokens from fragments / monkeypatch `HOME` and `socket.gethostname` at runtime in `tmp_path` fixtures | Rely only on ambient `Path.home()` and `socket.gethostname()` (fails in `/root` or `_GENERIC_DERIVED_TOKENS` containers); put literal `/home/<user>` in source (fails `aw sanitize` since test file is not in `_ALLOWED_PATHS`) | `agent_workflows/leak_sanitizer.py:120-146,478-513`; `tests/test_leak_sanitizer_machine_flags.py:99` | yes |
