# Review findings: ipd mnlaoa

- Subject-Id: mnlaoa
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261124T195133Z-1320375`). The target plan `.aw/records/plans/pending/20261122-selectors-02-mnlaoa-wire-normalized-artifact-selectors-into-query-and-mutation-c.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author` reported the plan conforming. The review read spec `ogd2nv` (R-02, R-05, R-06, AC-03, OQ-02), backlog item `1iojci`, the Order 01 plan `bzsoai` (its `add_selector_args`/`parse_selector_namespace`/`filter_records` API and its gate) and its review record, sibling plans `3xwbvs` (orchestrator) and `e36q6r`, the overlapping plan `p06t7i` (Set `cliverbs`), and the code each E-item touches: `agent_workflows/cli.py` (the noun-verb loop, the `aw att`, `aw partition`, `aw specs set`, `aw ipd board`, and `aw show` parsers and handlers, `_RunStatusAction`, `_reconstruct_apply_command`, `_run_find_impl`, the search handler), `agent_workflows/status_set.py` (`ArtifactRecord`, `_spec_date_refusal`, the date readers, `_RETRY_FLAG_ALLOWLIST`, `_retry_command`, `run_set_command`), `agent_workflows/partition.py`, `agent_workflows/meta_cli.py::index_alias`, `agent_workflows/plans_index.py::query`, `agent_workflows/artifact_rename.py`, `agent_workflows/plans_refs.py`, `agent_workflows/research_refs.py`, `agent_workflows/plans_archive.py`, and `agent_workflows/research_archive.py`. Parser facts came from argparse dumps of `cli._build_parser()` under `AW_NO_REEXEC=1`; release facts came from `git grep` at tag `v1.3.0-rc.1`.

### Step T

1. Yes; the plan changes public CLI options on about a dozen commands (new selector flags, `-p`/`-S`/`-d` meaning changes, `--date` renamed to `--history-date`) and amends spec `ogd2nv`.
2. Partly; it touches the bulk-write path of `aw set` and the `--apply` retry of `aw group`/`aw rename`, which decide which artifacts a mutation writes, but no commit, worktree, merge, or sandbox code.
3. Yes; after review it has 10 E-items in 3 task groups across 5 production modules and 15 test files.
4. Yes; `- Scope-Paths:` now lists every touched file (the original omitted `selectors.py`, the spec, and 12 test files).
5. Yes; a selector dest colliding with a write dest would write a filter value into an artifact, and a retry that drops a filter would widen a bulk rename.

AW-TIER: standard

### Step R1

- Checked: every command, flag, and dest the plan names against an argparse dump; every reader of `args.date`, `args.status`, `args.status_not`, `args.priority`, and `args.set` in the touched modules; `ogd2nv` R-05 against the parsers.
- Found that top-level `aw set` has no `--date` and the real history-date override is `aw specs set --date` (`PR-001`); that the noun-verb loop already registers `--status`, `--status-not/-S`, `--set`, and `--date` on `find`/`search`/`index`/`group`/`rename`, so wiring the builder raises `ArgumentError` unless those are deleted per verb (`PR-003`); that `aw search` also has `-p/--paths`, which spec R-05 omits (`PR-005`); that `--arcive-state` is already one alias of `--active-state` in a single `_RunStatusAction` call, so the "typo fix" is hiding the spelling (`PR-010`); and that the Step 0 footprint counts were wrong (`PR-012`).

### Step R2

- Checked: E/V bijection, dependency order, `- Item-Dependencies: executed:bzsoai`, each V-item's test home, and the validation commands.
- Found that V-03 asked `tests/test_cli_find.py` and `tests/test_attention.py` to prove `show`/`set`/`group`/`rename`/`archive`/`index`/`ipd board`, none of which those files exercise (`PR-012`); that `tests/test_normalized_selectors.py` is created by `bzsoai` and is not yet on disk (`PR-013`); that no item mapped the `ValueError` from `bzsoai` to exit 2 (`PR-014`); that the sanitizer was bare `aw sanitize`; and that the gate was one sentence (`PR-015`). After review: `10/10` bijection, `- Highest E allocated: 10`, and every new item was numbered by `aw ipd sync --apply`.

### Step R3

- Checked: the mutation verbs. `aw set` requires a positional target (`status_set.py` line 3133) and a confirmation for bulk writes (around line 3942); `aw group`/`aw rename` print an `--apply` command rebuilt from `sys.argv` by `_reconstruct_apply_command`.
- Found that `_reconstruct_apply_command` skips `-d` and its value as if it were `--dir`, though those parsers give `--dir` no `-d`, so a selector `-d 2026` would vanish from the printed `--apply` retry and the retry would rename more than the preview showed (`PR-006`). Found that the plan never said selector flags must only narrow a positional target set (`PR-006`). Found that `status_set.py` reads `args.priority` as a value to write (lines 1269, 1915, 3263, 3554), so an unprefixed selector `-p` on `aw set` would be written into artifacts (`PR-002`).

### Step R4

- Checked: per-command reader types (`find --status` and `ipd board --status` are single strings; `att`/`search`/`partition` status flags are lists), record sources, and cost.
- Found the `find`/`ipd board` single-value readers that an append flag would break (`PR-007`); that `aw index` lists nothing, so selectors would be inert there with no stated meaning (`PR-008`); that `aw show` and `aw archive` had no stated filter point (`PR-009`); that `status_set.ArtifactRecord` carries no priority, readiness, or attention class and `attention.scan` costs about 6.27 seconds against 0.8 to 1.2 seconds for a whole `aw find`, so a per-path adapter is needed (`PR-011`); and that `aw partition -t` is a single-tree selector that `-T` cannot meaningfully extend (`PR-004`).

### Step R7

- Checked: `bzsoai` (Order 01, `reviewed`, `go-pending-approval`) leaves the `ValueError`-to-exit-2 mapping and the `-o` help text to this plan; `e36q6r` (Order 03) owns completions, docs, and `tests/test_completion.py`, and its `- Scope-Paths:` omit `tests/test_record_builder_slow.py`, which this plan's original Deferred section had assigned to it; `p06t7i` (Set `cliverbs`, depends on `e36q6r`) later restructures `aw show`.
- Found that `bzsoai`'s API has no way to keep selector dests apart from write dests (`PR-002`; resolved by E-05 adding a defaulted `dest_prefix` keyword, which leaves `bzsoai`'s behavior unchanged); moved `tests/test_record_builder_slow.py` into this plan (`PR-012`); recorded the `p06t7i` overlap in `## Spec / documentation sync` (`PR-009`).

### Step S5

- Checked: `## Open questions` read "None", but the selector `-d/--date` collides with the existing mutation `--date` (new filename date) on `aw group`/`aw rename`. Choosing between renaming a public mutation flag and leaving those two verbs without the date filter is a public-interface decision for the maintainer, so it is escalated as blocking `OQ-01` (`- Finding: PR-004`, `- Owner: maintainer`, carried by backlog `1iojci`).
- Whether `aw specs set --date` keeps a hidden alias after the rename is non-blocking: the flag is absent from tag `v1.3.0-rc.1`, so no released user depends on it. It is recorded as a non-gating question in the outcome file, with the recommendation of no alias (weak strength), and the plan defaults to no alias.
- Every other finding was settled from repository evidence; design choices made at review are `D-1..D-5`.

### Pass 2

- Re-checked the complete revised plan: front matter, the common rules, `E-01..E-10`, Step 0, Findings, Proposed changes and its new Mermaid flowchart, Deferred, Scope check, Required tests, Spec sync, OQ-01, `V-01..V-10`, and the gate.
- Verified `10/10` E/V bijection, unchanged checkbox states, no `E-NEW` leaves left, no em or en dashes, and `aw ipd lint --phase review-finalize` reporting only `IPD-Q501` (the intended open blocking question) plus the advisory `IPD-Z603` size notes.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / Wrong rename target | argparse dump of `aw set` (`-m`, `-y`, `args` only); agent_workflows/cli.py:7890 (`aw specs set --date`); agent_workflows/status_set.py:1618-1620, 2212, 3125, ~2314; tests/test_event_overrides.py:227-252; spec `ogd2nv` R-05 | The plan (following spec R-05) renamed `aw set --date`, a flag that does not exist; the real override is `aw specs set --date`, with three readers, a retry allow-list entry, and refusal tests. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-09 retargets the rename to `aw specs set`/`aw spec set`, adds `--history-date` to `aw set`, updates readers, allow-list, refusal message, and tests; E-10 amends R-05 and AC-03. |
| PR-002 | HIGH | IN-SCOPE | R3 / Dest collision on `aw set` | agent_workflows/status_set.py:1269, 1915, 3263, 3554 (`args.priority` written), ~2314 (`args.status` echoed), 1618/2212/3125 (`args.date`) | Selector flags with the default dests would be read by the write path, so `aw set ... -p high` would write `Priority: high`. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-05 adds a defaulted `dest_prefix` to the `bzsoai` builder; E-09 attaches selectors with `dest_prefix="sel_"` to top-level `aw set` only, never to `specs`/`backlog`/`ipd set`. |
| PR-003 | HIGH | IN-SCOPE | R1 / Argparse conflicts | agent_workflows/cli.py:5518-5745 (noun-verb loop), 6098-6262 (`aw att`), 5309 (`aw partition`); measured `ArgumentError: argument -t/--type: conflicting option strings` | Each target parser already registers several selector option strings, so calling `add_selector_args` as written fails at parser build time for every `aw` command. | C:Low; U:Low; S:Low; Overall:Low | fixed | Common rule plus per-item lists of which registrations each E-item deletes, per verb, leaving `aw check` untouched. |
| PR-004 | HIGH | IN-SCOPE | R1 / Group and rename mutation `--date` | agent_workflows/cli.py:5695 (`--date` "Date (YYYYMMDD; default preserves existing date or today)"); agent_workflows/research_refs.py:765, 866 | On `group`/`rename`, `--date` sets the new filename date, so the selector `-d/--date` cannot be added without renaming a public mutation flag or exempting those verbs. | C:Low; U:Med; S:Low; Overall:Med | open | Blocking OQ-01 (owner maintainer, carrier `1iojci`); E-08 is written for either answer and V-08 checks the chosen one. |
| PR-005 | HIGH | IN-SCOPE | R1 / `aw search -p` | argparse dump (`search` has `-p/--paths`); tests/test_cli_search.py (16 uses of `-p`); spec `ogd2nv` R-05 | Spec R-05 moves only `search -S`, but `search -p` (paths) collides with selector `-p` (priority) the same way `find -p` does. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-07 drops `-p` from `--paths` on search; E-04 migrates the 16 test uses; E-10 adds it to R-05. |
| PR-006 | HIGH | IN-SCOPE | R3 / Mutation narrowing and `--apply` retry | agent_workflows/cli.py:15289-15320 (`_reconstruct_apply_command` skips `-d` plus value); agent_workflows/status_set.py:3133, ~3942 | Plan never required selector flags to only narrow a positional target set, and the `--apply` retry would drop a selector `-d` value and widen the rename. | C:Low; U:Low; S:Low; Overall:Low | fixed | Task-group 2 mutation safety rule; E-08 fixes `_reconstruct_apply_command`; E-09 extends `_retry_command` for `sel_*` lists; V-08/V-09 test both. |
| PR-007 | MEDIUM | IN-SCOPE | R4 / Single-value status readers | agent_workflows/plans_index.py:316-327; agent_workflows/cli.py:15963-15966, 16020-16024, 16733, 16856, ~16980; 12989-13012 (`status_filter`, `status_not_filter`) | `find --status` and `ipd board --status` are single strings consumed as strings; an append selector makes them lists. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-06 moves find filtering to `filter_records` and keeps `wja06w` validation; E-03 maps board values onto the existing `RECOGNIZED` check. |
| PR-008 | MEDIUM | IN-SCOPE | R4 / `aw index` meaning | agent_workflows/meta_cli.py:722-764 | `aw index` only rebuilds or checks the cache, so selector flags have nothing to narrow, and the plan gave them no meaning. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-03 accepts and ignores them with an info notice naming `aw find`, as `--limit` is treated; E-10 records it in R-06. |
| PR-009 | MEDIUM | IN-SCOPE | R4 / `show` and `archive` filter points | agent_workflows/cli.py:14359-14440 (`_run_show`, `resolve_selectors`, zero-match refusal); agent_workflows/plans_archive.py:206, 272, 449; agent_workflows/research_archive.py:265, 669; plan `p06t7i` | No filter point was named, and a filter that empties `aw show` hits would hit the "token names no artifact" refusal, which would be false. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-03 names the filter points and the empty-result behavior; spec-sync notes `p06t7i` must keep the flags. |
| PR-010 | MEDIUM | IN-SCOPE | R1 / `--arcive-state` | agent_workflows/cli.py:1372-1384, ~6248; agent_workflows/attention.py:4232, 5025; tests/test_attention.py:1876-1892, 3277-3279, 3364; tests/test_attention_excluded_tree_selector.py:87; tests/test_empty_result_convention_doc.py:117 | The misspelling is already one alias of `--active-state`; "fixing" it by renaming would break three test files that build namespaces with `arcive_state`. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-01 hides the spelling with `help=SUPPRESS` and keeps all three namespace attributes. |
| PR-011 | MEDIUM | IN-SCOPE | R4 / Record source and cost | agent_workflows/status_set.py:129 (`ArtifactRecord`); `artifact_meta.State.fields`; measured `attention.scan` about 6.27 s vs `aw find` 0.8-1.2 s | `filter_records` reads priority, readiness, and attention class, which the mutation and find record types lack, and the only scan that has them is slow. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-05 adds `selector_records(repo_root, paths)` reading `artifact_meta` per path; common rule skips filtering when no selector value is given. |
| PR-012 | MEDIUM | IN-SCOPE | R2 / Footprints and test homes | `grep` counts: tests/test_find_filters.py (19 `-p`), tests/test_cli_find.py (10), tests/test_cli_search.py (16 `-p`, `-S` at 198), tests/test_index_aliases.py:279, tests/test_record_builder_slow.py:56; e36q6r Scope-Paths | Step 0 counts were wrong, `tests/test_record_builder_slow.py` was deferred to a plan that does not declare it, and V-03 named test files that do not exercise the commands it covers. | C:Low; U:Low; S:Low; Overall:Low | fixed | Corrected Step 0; E-04 lists every moved-flag user; Scope-Paths adds 12 real test homes; V-01..V-10 each name their file. |
| PR-013 | MEDIUM | IN-SCOPE | R2 / Missing test file | `ls tests/test_normalized_selectors.py` (absent); bzsoai E-04 creates it | Validation named a file that exists only after `bzsoai` executes. | C:Low; U:Low; S:Low; Overall:Low | fixed | Kept, because `- Item-Dependencies: executed:bzsoai` guarantees it; E-05 adds its tests there. |
| PR-014 | LOW | IN-SCOPE | R2 / Exit code 2 | bzsoai E-01/E-02 (`ValueError` left to callers); spec `ogd2nv` R-03; agent_workflows/cli.py:~12996; agent_workflows/partition.py:1947, 2179 | No item mapped a selector `ValueError` to exit 2 with the token named. | C:Low; U:Low; S:Low; Overall:Low | fixed | Common rule gives the human and agent shapes; V-01/V-02/V-03 test an invalid expression. |
| PR-015 | LOW | IN-SCOPE | S7 / Gate, validation, carried text | plan gate (one sentence); `aw sanitize`; bzsoai E-03 (`-o` help text left to mnlaoa); core-marker facts | The gate lacked scope fence, safety, honesty, commit, and conditional lifecycle clauses; the sanitizer form, the `-o`/`m`-minutes help text, and core marking of new tests were missing. | C:Low; U:Low; S:Low; Overall:Low | fixed | Full gate added; `aw sanitize --agent`; E-01 carries the help text; common rule marks new test classes `core`. |
| PR-016 | MEDIUM | IN-SCOPE | R4 / Partition `-T` | agent_workflows/cli.py:5336-5345 (`-t` single `Store`, choices plans/backlog/specs); agent_workflows/partition.py:1891-1893 | `aw partition -t` picks the one tree a run schedules; the original plan required `-T`, which has no meaning there. | C:Low; U:Low; S:Low; Overall:Low | fixed | E-02 keeps partition's `-t` and uses `include_types=False`; E-10 records the exception in R-06. |
| PR-017 | LOW | IN-SCOPE | Plan size | `aw ipd lint` advisory `IPD-Z603` (10 E-items, 20 work Scope-Paths) | The hardened plan exceeds the size guidance. | C:Low; U:Low; S:Low; Overall:Low | deferred | Advisory only; each E-item is one surface with its own V-item. Scope check names a query/mutation split as an option for the approver. Carrier-Declined: advisory guidance, not a defect. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Scope`, `Scope-Paths` | `aw set --date` rename, 7 paths | Correct rename target, `dest_prefix`, `_reconstruct_apply_command`, spec amendment, exclusions; 22 paths | PR-001, PR-002, PR-006, PR-012 |
| Task group 1 | E-01 (att+find+search) and E-02 | Common rules; E-05 builder extension; E-01 att; E-06 find; E-07 search; E-02 partition | PR-002, PR-003, PR-005, PR-007, PR-010, PR-011, PR-014, PR-016 |
| Task group 2 | One E-03 for seven commands | Mutation safety rule; E-03 read-only verbs; E-08 group/rename; E-09 set | PR-001, PR-004, PR-006, PR-008, PR-009 |
| Task group 3 | E-04 tests in three files | E-10 spec amendment; E-04 moved-flag migration and full validation | PR-001, PR-005, PR-012 |
| Step 0, Findings, Proposed changes | Wrong counts, one finding, four lines | Measured parser facts, five findings, nine steps and a Mermaid dependency flowchart | PR-003, PR-012, technical writing standard requirement 12 |
| Required tests, V-01..V-10 | Three test files, bare `aw sanitize`, V-03 in wrong files | Every test home, bare core run, `aw specs check`, `aw sanitize --agent`, one named file per V-item | PR-012, PR-015 |
| Open questions, gate | "None"; one sentence | Blocking OQ-01; full execution contract | PR-004, PR-015 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| OQ-01 | E-08, spec `ogd2nv` R-05 | Whether `-d/--date` filters or sets a date on `aw group`/`aw rename` | Maintainer choice of public flag name | Rename the mutation option to `--new-date` (keep `dest="date"`) | medium |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How do selector dests stay clear of write dests on `aw set`? | Defaulted `dest_prefix` keyword on the `bzsoai` builder, used only by mutation verbs | An adapter namespace in `status_set.py` (rejected: two places spell selector dests); renaming write dests (rejected: wide churn) | PR-002 evidence; `bzsoai` behavior unchanged with `""` | yes |
| D-2 | Where does the `--history-date` rename land? | `aw specs set`/`aw spec set`, plus a new `--history-date` on top-level `aw set`; no hidden `--date` alias | Keep a hidden alias (left as a non-gating question) | PR-001; flag absent from `v1.3.0-rc.1` | yes |
| D-3 | What does `aw index` do with selector flags? | Accept and ignore them with an info notice | Refuse them (rejected: breaks the uniform grammar R-06 asks for) | `meta_cli.index_alias` lists nothing; `--limit` precedent | yes |
| D-4 | Does `aw partition` get `-T`? | No; keep its single-tree `-t` and use `include_types=False` | Multi-tree partition (rejected: breaks Set cohesion, out of scope) | PR-016 | yes |
| D-5 | How is `--arcive-state` fixed? | Hide it with `help=SUPPRESS`, keep all dests | Delete it (rejected: unannounced removal; tests construct its dest) | PR-010 | yes |
