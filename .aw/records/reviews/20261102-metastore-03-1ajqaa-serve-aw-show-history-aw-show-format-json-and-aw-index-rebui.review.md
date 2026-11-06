# Review findings: plan 1ajqaa

- Subject-Id: 1ajqaa
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `367944455` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 4) is byte-identical to the tracked plan, which was committed and unmodified, so no
pre-review snapshot was needed. `aw ipd lint --phase author` reported clean.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01, V-01, E-10, V-10 | Baseline under `/tmp/opencode`, `aw check` compared by counts | Baseline under `.aw/state/1ajqaa/before/`; `(location, rule)` diff | PR-005. |
| E-02 | Shows old filenames with the current name appended (AC-41 (4)) | Not done here; deferred to `dcerjg` | PR-004: contradicted the Deferred section. |
| E-03, V-03 | `--format {text,json}` default `text` | `default=None`, plus a test that `--agent --format json` keeps the conflict refusal | PR-001. |
| E-04 (b), E-08, V-04 | Fixture logs written with `artifact_meta.create`/`append` | Written directly with `artifact_meta.encode_event` | PR-002. |
| E-06, E-07, V-07 | Refresh placement unstated | In `cli._run_noun_verb` after the loop, best effort, output and exit code unchanged; new case (f) | PR-003. |
| E-09, V-09, E-10 | `RUNNABLE_ARGV` entries for `index rebuild` and `show --history` | No new key (the matrix is leaf-keyed); the two conformance modules run instead | PR-006. |
| Gate | Partial execution contract | Full contract, with `--scope-ack` for declared paths that may stay untouched | S7 rule (folded into PR-005). |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it adds a public CLI flag pair to `aw show`, a new `aw index rebuild` spelling and output records.
2. No.
3. Moderate: 10 E-items in 5 task groups, one new module plus `cli.py` wiring.
4. Yes: 12 Scope-Paths.
5. Yes: a mistake in `cli._run_show` or `_run_noun_verb` breaks `aw show` and `aw index`, which other code and the conformance sweep use; it is easy to revert.

AW-TIER: standard

### Step R1

- Checked by running in this lane: `aw show --help` (only `action_ref`, `--dir`); `cli._run_show` prints `read_text` per match and returns `{"matches", "contents"}` under `--agent`/`--json`; `aw show nosuch1 --agent` exits 2 with `unresolved_selectors`; `command_surface` `show` `exit_contract=(0, 2)` and `index` `(0, 1, 2)` with `legacy_flags`; `cli._run_noun_verb` calls `_nv_resolve_types`, which runs `artifact_types.normalize_type` and refuses `rebuild` today ("unknown artifact type 'rebuild'", exit 2; measured with `aw index rebuild --agent`), so routing before normalization is required as E-05 says; `aw index plans --agent` reports `applied: true` and INDEX `changes` (F-03 holds); `attention_contract.neutralize_control_characters` exists; `artifact_types.ARTIFACT_TYPES` has no `rebuild`; `tests/conformance_matrix.py` `RUNNABLE_ARGV` has `"show": ["f36de0"]` and `"index": ["plans", "--check"]`; `tests/test_cli_show.py` has 6 tests and Case 6 asserts observed exits `{0, 2}`; the cited test modules exist; `rg -n "[\u2013\u2014]"` matches an em dash (V-09's check works).
- `result_types.select_output`: a non-None `format` other than `json` beside `--agent` or `--json` raises `ConflictingFlagsError` (measured with `Namespace(agent=True, format='text')`). This is PR-001.

### Step R2

- Checked: E/V bijection 10/10; each V demands pasted test runs, diffs or records; reachability is by construction. Scope-Paths covers the edits (`plans_index.py` and siblings are not edited once the refresh lives in `cli.py`, PR-003). `- Item-Dependencies: executed:tve77h` is correct. `RUNNABLE_ARGV` is keyed by parser leaf (`command_surface.discover_parser_leaves`; read in `tests/test_agent_surface_conformance.py` as `RUNNABLE_ARGV.get(leaf, [])`), so the planned `index rebuild` key would never be read (PR-006).

### Step R3

- Checked: read-only verbs plus a gitignored cache rebuild; imported legacy text is neutralized for display (E-02); no secrets, network or privileged paths. No finding.

### Step R4

- Checked: A, `aw index rebuild` writes only the gitignored cache and E-07 (b) proves no tracked file changes. C, reuses `CommandResult`, the renderers and the selector refusal; `meta_cli.py` is also extended by `ffceq0` (E-10, E-11) and `9o83cr`, consistent with this plan creating it. D, the no-flag `aw show` and `aw index plans --check` invariants are diffed against the baseline. Two problems: the `text` default would break every `--agent`/`--json` call (PR-001), and the refresh in the typed spellings had no failure rule, so an invalid record could change `aw index plans` output or exit code, contrary to E-06's own byte-identical claim (PR-003). E, cold/warm/deleted/corrupt/external-edit cases present. F, docs and CHANGELOG are user-facing and the no-dash rule is checked. Spec sync claim is truthful.

### Step R7

- Checked siblings: `2xwb9b` E-03 makes `artifact_meta.append` dispatch on `_storage_format(records_root)`, which returns `legacy` until Order 13. `2xwb9b` runs after this plan, but this plan's tests stay in the core suite, so a fixture that builds its log through `append`/`create` stops producing a log once `2xwb9b` lands, breaking E-04 (b) and E-08 on `main` (PR-002). `9o83cr` E-02 later converts the typed spellings to aliases of `meta_cli.index_rebuild` (consistent with OQ-01 and the Deferred carrier). `cxxmyv` re-demonstrates AC-2 on the real repository (consistent). `dcerjg` owns the rename map that AC-41 (4) display needs, so E-02's display rule contradicted the Deferred row (PR-004).

### Step S5

- Checked: OQ-01 and OQ-02 resolved, non-blocking, still valid. No new human question. Decisions below.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R4 D regression | `result_types.select_output` "conflicting output format flags: cannot combine --agent and --format"; plan E-03 "`--format {text,json}` (default `text`)" | A `text` default puts `format='text'` on every parse, so `aw show <ref> --agent` and `--json` would raise and exit 2. That breaks the conformance row `"show": ["f36de0"]` and E-03's own byte-identical claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `default=None`; E-03 and V-03 assert the baseline outputs are unchanged and that `--agent --format json` still refuses. |
| PR-002 | MEDIUM | IN-SCOPE | R7 cross-plan | `2xwb9b` E-03 "`_storage_format(records_root)` returning `legacy` until Order 13" | E-04 (b) and E-08 built log fixtures through `artifact_meta.create`/`append`, which will write the legacy format once `2xwb9b` lands. Those core tests would then fail or stop testing logs. | Low | FIXED | Fixtures write `meta/<id6>.jsonl` with `artifact_meta.encode_event`; V-04 quotes the fixture code. |
| PR-003 | MEDIUM | UNDER-SCOPE | R4 D / scope | plan E-06 "call `artifact_meta`'s freshness pass"; Scope-Paths lacks `plans_index.py` | The plan did not say where the refresh runs or what happens when it fails. A raising refresh would change the typed spelling's output or exit code. | Low | FIXED | The refresh runs in `cli._run_noun_verb` after the loop, without `--check`, and swallows errors; new E-07 case (f). |
| PR-004 | LOW | IN-SCOPE | P consistency | plan E-02 "AC-41 (4) display rule" vs Deferred "Carrier: dcerjg" | E-02 required a behavior that the plan also deferred. | Low | FIXED | E-02 now states that the behavior is deferred. |
| PR-005 | MEDIUM | IN-SCOPE | G executability / S7 | E-01 "`/tmp/opencode/1ajqaa-before/`"; gate | The baseline was written outside the lane workspace, the `aw check` comparison used bare counts, and the gate lacked the full execution contract. | Low | FIXED | Baseline moved under `.aw/state/1ajqaa/before/`; `(location, rule)` diff; gate rewritten. |
| PR-006 | LOW | IN-SCOPE | R2 conformance | `tests/test_agent_surface_conformance.py` "`RUNNABLE_ARGV.get(leaf, [])`" | `index rebuild` and `show --history` are not parser leaves, so the planned `RUNNABLE_ARGV` keys would never be read. | Low | FIXED | No key is added; E-10 and V-09 run the two conformance modules. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Default of `aw show --format` | `None` | `text` (breaks `--agent`/`--json`); dropping `text` from choices | `result_types.select_output` conflict rule, measured | yes |
| D-2 | Where the typed-spelling cache refresh runs | `cli._run_noun_verb`, best effort | Inside each `*_index.run_index` (three out-of-fence modules) | Scope-Paths; E-06 byte-identical requirement | yes |
| D-3 | How the log fixtures are produced | `artifact_meta.encode_event` lines written by the test | `artifact_meta.create`/`append` | `2xwb9b` E-03 format dispatch | yes |
