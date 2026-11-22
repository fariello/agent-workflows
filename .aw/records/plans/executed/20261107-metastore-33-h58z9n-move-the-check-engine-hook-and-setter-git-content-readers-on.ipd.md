# IPD: Move the check_engine, hook and setter git-content readers onto read_at

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 4.4 requires every reader of a HEAD, staged or branch revision to call `artifact_meta.read_at` instead of parsing git content, and C5a requires every gate and hook to read metadata through the cache. Measured 2026-11-07 at `ac76110f4`: `check_engine._blob_text` (`git show <ref>:<path>`, `:0:<path>`) has 12 call sites in 6 functions across `check_engine`, `hooks/ipd_dependency_statement_gate` and `status_set`, and `check_engine._status_meta` has 35 call sites in 13 functions; `hooks/executed_transition_gate` reads blobs with its own `_blob_at`; `plan_readiness.review_staleness_index` uses `git cat-file --batch`; `ipd_lifecycle._release_own_plan_edit_before_landing` uses `git show <landed>:<path>`. Part 1 of the split of `t4gl15` (Order 09), whose single plan hid several hundred units of work.
- Scope: FINISHING PART after the round-3 split (2026-11-09, research `nj8zdp` guidance). The baseline, the 4.4 search rows and the `check_engine` and hook moves (former E-01 baseline and gate-file rows, E-02, E-03) moved to `snh19k` (Order 145); the remaining 4.4 search rows and the setter, staleness, lifecycle and runner merge-path moves (former E-01 remaining rows, E-04) moved to `iqhzse` (Order 146). This plan keeps E-05: the residual-audit rows of `t4gl15` E-15 for the hook, readiness and lifecycle modules, the re-run of every moved module, and the gates. EXCLUDES: every other runner read (Order 34 `y97k46`), the record, review and orchestration modules (Orders 35 `jd7874` and 36 `2zpw22`), the new `meta/*.jsonl` append hook (`jq82as`), the cache-parity and offline tests and the repo-wide finish (`t4gl15`).
- Scope-Paths: .aw/records/plans/pending/20261107-metastore-33-h58z9n-move-the-check-engine-hook-and-setter-git-content-readers-on.ipd.md
- Scope-Exceeded: .aw/records/backlog/open/20261121-q4gwp9-01-q4gwp9-migrate-ipd-lifecycle-plan-status-event-groups-and.backlog.md (Defect-report backlog item filed during h58z9n E-05 residual audit per mandatory defect_report contract for unmigrated ipd_lifecycle._plan_status_event_groups and HISTORY_RECORD_RE callers before Orde...)
- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:snh19k, executed:iqhzse
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 33
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: h58z9n

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 executed (aw agy run model=Gemini-4-Neon-High): aw agy run self-finalize: h58z9n verified (set metastore, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261121-q4gwp9-01-q4gwp9-migrate-ipd-lifecycle-plan-status-event-groups-and.backlog.md: Defect-report backlog item filed during h58z9n E-05 residual audit per mandatory defect_report contract for unmigrated ipd_lifecycle._plan_status_event_groups and HISTORY_RECORD_RE callers before Order 11 tdhav3]
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01, E-02, E-03 moved to snh19k; E-01 (remaining search rows) and E-04 moved to iqhzse.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from t4gl15 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

Every gate, hook, setter and runner merge path that reads metadata out of a git revision (HEAD, the index, a commit, a merge stage) reads it through `artifact_meta.read_at`, with each moved reader's verdict pinned by a behavioral test before and after the move. After the round-3 split the moves are done by `snh19k` and `iqhzse`; this plan audits what remains in the hook, readiness and lifecycle modules and re-runs every moved module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies to every move here (carried from `t4gl15`): BEFORE the edit, a behavioral test in the named module pins the reader's current observable behavior (the ledger in `## Findings`) and runs green on the unmodified code; AFTER the edit, the same test runs unchanged. A test that must change is a behavior change and must be one of `t4gl15`'s decisions D-1 to D-4 (copied below). For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it, where `<E>` is the ORIGINAL `t4gl15` item id named in each item below; `diff` of the two prints nothing except lines a named decision explains. Run a new module's `-k` selection as its own command, never combined with baseline module paths, because `-k` filters every path on the command line. Every saved baseline goes under `.aw/state/t4gl15/`, never `/tmp`. New test modules set `pytestmark = pytest.mark.core` unless they need real `git` subprocesses across many commits, in which case they are marked `slow` and run in `make test-all`; none reads production source.

Round-3 note (2026-11-09): Task groups 1 and 2 (E-01 to E-04) moved to `snh19k` and `iqhzse`, both `- Item-Dependencies:` edges of this plan, so E-05's former `Depends on: E-03, E-04` is carried by those edges.

### Task group 3: residual audit and finish

- [x] E-05 (carried from `t4gl15` E-15, this plan's module subset) Run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" <files>` and `rg -n "Workflow history" <files>` over `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/status_untooled_gate.py`, `agent_workflows/plan_readiness.py` and `agent_workflows/ipd_lifecycle.py` (31 hits in 17 functions measured at `ac76110f4`; the `check_engine` and `status_set` rows belong to `ffceq0`'s residual table F-12, because both modules are in `ffceq0`'s scope, and `runner_shared` rows to Order 34 `y97k46`), and write table F-04 in this plan listing every remaining hit with its owner: writer (Orders 06/07, named), body-prose bullet kept by N3 (named pattern), a working-tree reader owned by `ffceq0` (named), or a parser that Order 11 deletes. A reader hit with no such owner is a defect of this plan and is moved before finishing. Run every module named in `snh19k` E-03 and E-04 and `iqhzse` E-02 and E-03 again (the moved `h58z9n` E-02 to E-04), the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit h58z9n -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: none
  - Expected outcome: F-04 has no unowned reader hit; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`), used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)`, `artifact_meta.resolve(path_or_id6)`, and `artifact_meta.read_at(id6, rev)`, which runs git in the repository that owns the resolved records root, resolves the record's path inside that revision (`git ls-files -s` for the index, `git rev-parse <rev>:<path>` for a commit), caches by blob sha in `rev_log_states`/`rev_mirrors`, feeds a miss to the same loader (the legacy loader for a bullet blob in phase B), fails closed on a validation error, and returns distinct results for an absent record, an invalid revision and an unversioned placement. From Order 08 (`ffceq0`): `artifact_meta.read_text(text, *, record_type=None) -> State` and decision D-1 (canonical normalized status for multi-word plans).
- Today's git-content helpers: `check_engine._blob_text(repo_root, ref, path)` (`git show <ref>:<path>`, `:0:<path>` for the index) and `check_engine._status_meta(text)`; `hooks.executed_transition_gate._blob_at`.
- The hooks are thin: `hooks.status_untooled_gate.check` delegates to `check_engine.check_status_untooled`, and `hooks.backlog_blocking_close_gate.check` filters `check_engine.check_release_gate_consistency`; both are dispatched by `cli` (`ipd-status-untooled-gate`, `backlog-blocking-close-gate`, `ipd-executed-gate`, `ipd-dependency-statement-gate`) and installed as optional pre-commit hooks from the `engine` template.
- Core tier: `pytestmark = pytest.mark.core`; tests needing many real git commits use the `slow` marker and run in `make test-all`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4` (the split measurement); F-02 is copied from `t4gl15` (measured 2026-11-02 at `0cbfcc706`).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n "_blob_text\(\|_status_meta\(" agent_workflows` prints 39 lines: the two definitions, 12 `_blob_text` calls (in `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition` 8, `_lane_carrier_is_executed`, `check_release_gate_consistency`, `hooks.ipd_dependency_statement_gate._staged_ipd_overlay`, `status_set._prepare_status_change`) and `_status_meta` calls in 13 functions | E-02 moves 6 `check_engine` callers; E-03 and E-04 move the other two. |
| F-02 | (from `t4gl15`) git-content metadata readers moved by this plan: `check_engine._blob_text` callers `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, `check_release_gate_consistency` (via `_staged_backlog_done_items`); `hooks.executed_transition_gate._blob_at`; `hooks.ipd_dependency_statement_gate._staged_ipd_overlay`; `status_set._prepare_status_change`; `plan_readiness.review_staleness_index` (`git cat-file --batch`); `ipd_lifecycle._release_own_plan_edit_before_landing` (`git show <landed>:<path>`); `runner_shared.backlog_item_paths_for_commit` (`git show <sha>:<path>` then `backlog.parse_item`), `check_review_lane_artifacts` (`git show <branch>:<path>`), `read_merge_stage`, `classify_conflict_set_for_rederivation` (`git cat-file -p`), `integrate_lane_branch` (`git cat-file -p <tree>:<path>` then `check_engine._metadata_status`) | All 15 functions of the 4.4 list. |
| F-03 | (written by `snh19k` E-02 and `iqhzse` E-01 in their own plans since the round-3 split; formerly E-01 here) the re-run 4.4 search over this plan's six files, each hit classified, and the merge-stage path chosen (OQ-02 of `t4gl15`). Measured at the split: 44 hits (`check_engine` 11, `hooks/executed_transition_gate` 8, `hooks/ipd_dependency_statement_gate` 2, `plan_readiness` 2, `ipd_lifecycle` 17, `artifact_meta` 4) | 4.4 says the list is a minimum. |
| F-04 | Executed 2026-11-22 at `706deceea` (E-05): 21 total hits across the four audited modules (5 `^-` regex hits, 16 `Workflow history` hits): `agent_workflows/hooks/executed_transition_gate.py` 1 (0 regex, 1 history), `agent_workflows/hooks/status_untooled_gate.py` 3 (0 regex, 3 history), `agent_workflows/plan_readiness.py` 11 (5 regex, 6 history), `agent_workflows/ipd_lifecycle.py` 6 (0 regex, 6 history); down from 31 at `ac76110f4`. Every hit is classified with its owner in Table F-04 below; 0 unowned git-revision reader hits. | Input to `t4gl15` E-15 and Order 11 (`9o83cr`); filed backlog `q4gwp9` for the Order 11 `ipd_lifecycle._plan_status_event_groups` / `HISTORY_RECORD_RE` migration gap. |
| F-10 | (written by `snh19k` E-01 in `snh19k` since the round-3 split; formerly E-01 here) rule-id counts of `aw check all --agent` before any edit of the `t4gl15` split | Baseline for `t4gl15` E-15. |

### Table F-04: Residual `^-` regex and `Workflow history` audit (E-05, commit `706deceea`, 21 hits)

Per-module hit counts:
- `agent_workflows/hooks/executed_transition_gate.py`: 1 hit (0 `^-` regex, 1 `Workflow history`; down from 2 at `ac76110f4` after `snh19k` E-04 moved `_plan_id_of` onto `artifact_meta`).
- `agent_workflows/hooks/status_untooled_gate.py`: 3 hits (0 `^-` regex, 3 `Workflow history`; unchanged from 3 at `ac76110f4`).
- `agent_workflows/plan_readiness.py`: 11 hits (5 `^-` regex, 6 `Workflow history`; down from 16 at `ac76110f4` after `d4w53g` moved the writer and `iqhzse` E-02 deleted `_STATUS_RE`).
- `agent_workflows/ipd_lifecycle.py`: 6 hits (0 `^-` regex, 6 `Workflow history`; down from 10 at `ac76110f4` after `8q27jt` moved `_insert_scope_exceeded_metadata` onto `artifact_meta.append`).

| # | File and symbol | Query | Matched code | Class | Owner / Action |
|---|---|---|---|---|---|
| 1 | `agent_workflows/hooks/executed_transition_gate.py` (module docstring, line 14) | `Workflow history` | `SAME \`- Id:\` and is merely EDITED - a body correction, an appended \`## Workflow history\` line. Nothing` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion) / Order 12 (`90iqr1`). |
| 2 | `agent_workflows/hooks/status_untooled_gate.py` (module docstring, line 10) | `Workflow history` | `matching tool-authored \`## Workflow history\` transition line for the new status, REFUSES the commit` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion) / Order 12 (`90iqr1`). |
| 3 | `agent_workflows/hooks/status_untooled_gate.py` (module docstring, line 24) | `Workflow history` | `are examined - history-less types (prompts/releases) carry no \`## Workflow history\` and are excluded.` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion) / Order 12 (`90iqr1`). |
| 4 | `agent_workflows/hooks/status_untooled_gate.py::main` (line 104) | `Workflow history` | `"changed with no attributed \`## Workflow history\` line - it looks hand-edited):\n"` | CLI refusal prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion); post-cutover wording owned by Order 12 (`90iqr1`) / Order 13 (`cxxmyv`). |
| 5 | `agent_workflows/plan_readiness.py::_READINESS_FIELD_PRESENT_RE` (line 263) | `^-` regex | `_READINESS_FIELD_PRESENT_RE = re.compile(r"(?m)^-[ \t]*Readiness:")` | parser Order 11 deletes | Working-tree / in-memory text predicate (`is_plan_review_approved`, `approval_refusals`, `recheck_conditions`), not a git-revision reader; deleted by Order 11 (`9o83cr` / `0xsx2n` / `akhrp5` Order 247 E-01). |
| 6 | `agent_workflows/plan_readiness.py::_OQ_FIELD_RE` (line 266) | `^-` regex | `_OQ_FIELD_RE = re.compile(r"^-[ \t]*([A-Za-z][A-Za-z /-]*?):[ \t]?(.*)$")` | body-prose bullet kept by N3 | Parses `- Blocking:` and `- Status:` sub-bullets inside `## Open questions` (`has_unresolved_blocking_question`, `review_staleness_from_texts`); explicitly kept by N3 (`akhrp5` E-01, `9o83cr` E-14). |
| 7 | `agent_workflows/plan_readiness.py::approval_refusals` (line 719) | `^-` regex | `id6_match = re.search(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$", plan_text)` | parser Order 11 deletes | Working-tree / in-memory text reader, not a git-revision reader; explicitly deleted by Order 11 (`9o83cr` / `0xsx2n` / `akhrp5` Order 247 E-01). |
| 8 | `agent_workflows/plan_readiness.py::recheck_conditions` (line 909) | `^-` regex | `id6_match = re.search(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$", plan_text)` | parser Order 11 deletes | Working-tree / in-memory text reader, not a git-revision reader; explicitly deleted by Order 11 (`9o83cr` / `0xsx2n` / `akhrp5` Order 247 E-01). |
| 9 | `agent_workflows/plan_readiness.py::_READINESS_LINE_SUB_RE` (line 1350) | `^-` regex | `_READINESS_LINE_SUB_RE = re.compile(r"(?m)^-[ \t]*Readiness:[ \t]*.*$")` | writer leftover (Order 07) / Order 11 deletes | Writer moved onto `artifact_meta.append` in Order 07 (`xexn45` / `d4w53g` E-01); 0 production callers (imported only by `tests/test_plan_readiness_recheck.py`); deleted by Order 11 (`9o83cr` / `0xsx2n` / `akhrp5` Order 247 E-01 and E-05). |
| 10 | `agent_workflows/plan_readiness.py` (module docstring, line 12) | `Workflow history` | `The old \`\`extract_last_history_entry\`\` did \`\`text[text.rfind("## Workflow history"):]\`\` with NO` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion). |
| 11 | `agent_workflows/plan_readiness.py` (module docstring, line 33) | `Workflow history` | `\`\`## Workflow history\`\` contains a REVIEW RECORD that could have produced it` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion) / Order 12 (`90iqr1`). |
| 12 | `agent_workflows/plan_readiness.py::extract_newest_history_entry` (docstring, line 270) | `Workflow history` | `"""The NEWEST \`\`## Workflow history\`\` record of \`\`text\`\`, or None when there is none.` | docstring prose | Docstring only; function delegates to `attention_contract.history_block`, moved onto `artifact_meta` by Order 11 (`k6jd6l` / `ay6sxp` Order 291 E-01). |
| 13 | `agent_workflows/plan_readiness.py::is_plan_review_approved` (docstring, line 394) | `Workflow history` | `the answer is, but only once the plan's own \`\`## Workflow history\`\` shows a review PRODUCED it;` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion) / Order 12 (`90iqr1`). |
| 14 | `agent_workflows/plan_readiness.py::history_has_review_record` (docstring, line 552) | `Workflow history` | `"""Whether ANY record in the plan's bounded \`\`## Workflow history\`\` is a REVIEW record.` | docstring prose | Docstring only; function delegates to `attention_contract.history_block`, moved onto `artifact_meta` by Order 11 (`k6jd6l` / `ay6sxp` Order 291 E-01). |
| 15 | `agent_workflows/plan_readiness.py::format_recheck_history_entry` (docstring, line 1167) | `Workflow history` | `"""Render the \`## Workflow history\` record for a performed re-check, carrying its evidence.` | docstring prose | Docstring of Order 07 writer helper (`d4w53g` E-01 moved `recheck_readiness` onto `artifact_meta.append`); Order 11 (`9o83cr` E-14 exclusion). |
| 16 | `agent_workflows/ipd_lifecycle.py::frozen_region_digest` (docstring, line 929) | `Workflow history` | `\`\`Observed evidence\`\`/\`\`Result\`\`, append a \`\`## Workflow history\`\` line), so the byte digest always` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion). |
| 17 | `agent_workflows/ipd_lifecycle.py::frozen_region_digest` (docstring, line 950) | `Workflow history` | `\`\`Result:\`\`, \`\`Observed evidence:\`\`), the \`\`## Workflow history\`\`, and the \`\`[ ]\`\`/\`\`[x]\`\` checkbox` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion). |
| 18 | `agent_workflows/ipd_lifecycle.py` (comment above `LIFECYCLE_EVENTS`, line 1116) | `Workflow history` | `# parallel log, DECISION 16-wqj1ne-D1): for a PLAN the events are its inline \`## Workflow history\`` | comment prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion). |
| 19 | `agent_workflows/ipd_lifecycle.py::_plan_status_event_groups` (docstring, line 1346) | `Workflow history` | `Splits ## Workflow history into contiguous blocks separated by BLANK lines (indented continuation` | docstring prose | Docstring of `_plan_status_event_groups` (see row 20). |
| 20 | `agent_workflows/ipd_lifecycle.py::_plan_status_event_groups` (line 1369) | `Workflow history` | `if line.strip() == "## Workflow history":` | working-tree reader (`ffceq0` `check_engine` scope) / Order 11 parser cleanup | Called only by `check_engine._walk_plan_lifecycle_history` for working-tree rules `check_engine.check_lifecycle_transitions` and `check_lifecycle_transition_coverage` (`ffceq0` `check_engine` scope, not a git-revision `read_at` reader); relies on Markdown blank-line block boundaries and `attention_contract.HISTORY_RECORD_RE` (deleted by Order 11 `tdhav3` Order 248 E-02). Order 11 follow-up gap filed as backlog `q4gwp9` ahead of `tdhav3` and `9o83cr` E-14. |
| 21 | `agent_workflows/ipd_lifecycle.py::receipt_is_current` (docstring, line 1657) | `Workflow history` | `\`\`Observed evidence\`\`/\`\`Result\`\`, append a \`\`## Workflow history\`\` line), which always changed the` | docstring prose | Non-reader / non-writer; Order 11 (`9o83cr` E-14 exclusion). |

READER LEDGER (this plan's rows, copied from `t4gl15`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `check_engine.check_status_untooled` and `_range` | HEAD vs staged `- Status:` via `_blob_text` + `_status_meta`; refuse with no matching history line | E-02 fixtures; `tests/test_check_engine_status_meta.py`, `tests/test_precommit_scope_gate_severity.py` | same verdicts via `read_at` states and their history |
| `check_engine.check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, `check_release_gate_consistency`, `_lane_carrier_is_executed` | staged/HEAD backlog and carrier status via git blobs | E-02 fixtures; `tests/test_check_engine_release_gate.py`, `tests/test_backlog_close_gate_prose.py` | same via `read_at` |
| `hooks.executed_transition_gate` | case-insensitive region `status: executed\|done`, `- Id:` outside fences, finalize evidence | `tests/test_executed_transition_gate.py`, `tests/test_executed_transition_gate_e2e.py` | same via `read_at`; D-2 for case |
| `hooks.ipd_dependency_statement_gate` | staged `- Status:` and `Item-Dependencies` overlay | `tests/test_ipd_dependency_statement_gate.py` | same via `read_at(":0:")` |
| `status_set._prepare_status_change` HEAD read | HEAD `- Status:` of the plan path | `tests/test_status_set.py` | `read_at(id6, "HEAD")` |
| `plan_readiness.review_staleness_index` | status at latest `plan-review:` commit plus frozen-region body digest | `tests/test_review_staleness_advisory.py` | status via `read_at`; body digest unchanged (N3) |
| `runner_shared` git readers | backlog id from commit blob, review-lane plan checks, merge-stage keys, conflict status | `tests/test_runner_backlog_close_behavior.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_merge_conflict_sendback.py` | `read_at` or `read_text` |
| `ipd_lifecycle._release_own_plan_edit_before_landing` | byte equality of landed blob vs mirrored bytes | `tests/test_ipd_lifecycle_cli.py` | unchanged (not a metadata read); recorded in F-03 |

DECISIONS (copied from `t4gl15`; authoritative text stays there): D-1 multi-word status (plan records return the canonical normalized status); D-2 the executed-transition hook's case-insensitive match is preserved because the cached status is canonical lower-case.

## Proposed changes (ordered, validatable)

1. Run residual audit across hook, readiness, and lifecycle modules, populating table F-04 (E-05).
2. Re-run test suites across all moved modules, verify gates, and commit (E-05).

```mermaid
flowchart TD
    A["E-05: Run regex scans across target modules"] --> B["E-05: Populate table F-04 with hit owners"]
    B --> C{"Any unowned reader defect?"}
    C -->|Yes| D["Repair unowned reader via artifact_meta.read_at"]
    C -->|No| E["Re-run baseline suites for moved modules"]
    D --> E
    E --> F["Verify core test gate and commit path-scoped"]
```

## Deferred / out of scope (with reason)

- E-01 (the split-wide `aw check` baseline and table F-10, and the 4.4 search rows for `check_engine` and the two blob-reading hooks), E-02 (the `check_engine` git readers) and E-03 (the four hooks). Moved to snh19k (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: snh19k
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-145-snh19k-save-the-read-at-split-baseline-and-move-the-check-engine-an.ipd.md
- E-01 (the 4.4 search rows for `plan_readiness`, `ipd_lifecycle`, `artifact_meta` and `status_set`) and E-04 (the setter, staleness, lifecycle and runner merge-path readers). Moved to iqhzse (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: iqhzse
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-146-iqhzse-move-the-setter-staleness-lifecycle-and-runner-merge-path-gi.ipd.md
- The 4.4 search rows for `runner_shared`/`oc_runipd`/`agy_runipd`, the runner selection and execution reads, the own-log finalize scope, and the runner residual rows.
  - Carrier: y97k46
- The 4.4 search rows for the other 31 files, and the plans, research and prompts module reads.
  - Carrier: jd7874
- The review, orchestration, production-check and work module reads.
  - Carrier: 2zpw22
- The `meta/*.jsonl` append hook, the gate cache-parity and offline tests, the repo-wide residual audit and the `CHANGELOG.md` line.
  - Carrier: t4gl15

## Scope check

- Over-scope: none. This plan edits no code; it writes table F-04 into itself and moves any unowned reader hit it finds (a defect), which the finalize scope reconciliation then records.
- Under-scope: none known; E-05 exists to find what the measurement missed. Size after round 3: 1 E-item, 0 work Scope-Paths.

## Required tests / validation

No new test module (`tests/test_readers_read_at_gates.py` is created by `snh19k` and extended by `iqhzse`). CONTRIBUTES to `4sd62s` AC-16 and AC-33 through those parts. Commands: every module named in `snh19k` E-03/E-04 and `iqhzse` E-02/E-03, the bare core gate `python3 -m pytest`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change. Implements the gate, hook, setter and merge-path part of `4sd62s` 4.4 and C5a. CONTRIBUTES to AC-3 and AC-17 (merge-path readers through `read_at`; owned by `xexn45` and `tve77h`).

## Open questions

### OQ-01: Where do the split-wide baselines live?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `.aw/state/` is gitignored, so a baseline saved inside an isolated lane worktree does not reach a later plan. `snh19k` E-01 (formerly E-01 here) therefore also pastes the `aw check all --agent` rule-id counts into `snh19k` (F-10), which is tracked; `t4gl15` E-15 compares against F-10. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-05 validates E-05
  - Required evidence: paste the two `rg` commands of E-05 and the F-04 table with a per-module hit count for each of `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/status_untooled_gate.py`, `agent_workflows/plan_readiness.py` and `agent_workflows/ipd_lifecycle.py` (every remaining hit with its owner, none unowned); the summary line of each re-run baseline module of `snh19k` E-03/E-04 and `iqhzse` E-02/E-03, named one per line with 0 failed; the bare `python3 -m pytest` summary line and wall time; the `aw sanitize --agent` result with zero `fail`; and every `aw commit h58z9n` output listing only Scope-Paths (or paths justified at finalize).
  - Observed evidence:
    - E-05 residual `rg` commands (at commit `706deceea`):
      - `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/hooks/executed_transition_gate.py agent_workflows/hooks/status_untooled_gate.py agent_workflows/plan_readiness.py agent_workflows/ipd_lifecycle.py` -> 5 hits (all in `agent_workflows/plan_readiness.py`; 0 in the other three modules).
      - `rg -n "Workflow history" agent_workflows/hooks/executed_transition_gate.py agent_workflows/hooks/status_untooled_gate.py agent_workflows/plan_readiness.py agent_workflows/ipd_lifecycle.py` -> 16 hits (`executed_transition_gate.py` 1, `status_untooled_gate.py` 3, `plan_readiness.py` 6, `ipd_lifecycle.py` 6).
      - Per-module totals (21 hits total, all classified with owners in Table F-04 above, 0 unowned git-revision reader hits): `agent_workflows/hooks/executed_transition_gate.py`: 1 (0 regex, 1 history); `agent_workflows/hooks/status_untooled_gate.py`: 3 (0 regex, 3 history); `agent_workflows/plan_readiness.py`: 11 (5 regex, 6 history); `agent_workflows/ipd_lifecycle.py`: 6 (0 regex, 6 history). Order 11 follow-up gap on `ipd_lifecycle._plan_status_event_groups` and `attention_contract.HISTORY_RECORD_RE` callers filed as backlog `q4gwp9`.
    - Re-run of all 14 moved baseline modules named in `snh19k` E-03/E-04 and `iqhzse` E-02/E-03 (`python3 -m pytest -m "" <mod>`, 411 passed, 0 failed):
      - `tests/test_readers_read_at_gates.py`: `17 passed in 6.73s`
      - `tests/test_check_engine_status_meta.py`: `5 passed in 3.46s`
      - `tests/test_check_engine_release_gate.py`: `53 passed in 6.25s`
      - `tests/test_precommit_scope_gate_severity.py`: `8 passed in 2.58s`
      - `tests/test_backlog_close_gate_prose.py`: `3 passed in 2.20s`
      - `tests/test_executed_transition_gate.py`: `12 passed in 1.73s`
      - `tests/test_executed_transition_gate_e2e.py`: `7 passed in 5.11s`
      - `tests/test_ipd_dependency_statement_gate.py`: `17 passed in 2.65s`
      - `tests/test_review_staleness_advisory.py`: `13 passed in 7.69s`
      - `tests/test_ipd_lifecycle_cli.py`: `73 passed in 15.66s`
      - `tests/test_status_set.py`: `110 passed in 14.85s`
      - `tests/test_records_only_lane_rederive.py`: `34 passed in 2.87s`
      - `tests/test_runner_backlog_close_behavior.py`: `48 passed in 10.64s`
      - `tests/test_merge_conflict_sendback.py`: `11 passed in 15.86s`
    - Core tier gate (`aw suite` / bare `python3 -m pytest`): `2665 passed, 1 skipped, 11 warnings in 170.13s (0:02:50)` (exit 0; host 1-minute load average 21.82 on 12 CPUs).
    - Leak scan (`aw sanitize --agent`): `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":7046,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - Path-scoped `aw commit h58z9n` commits: `cb11d049f214dde89b7911f2956b8df077eddd39` (`aw commit h58z9n: committed 1 path(s)` for defect-report backlog item `.aw/records/backlog/open/20261121-q4gwp9-01-q4gwp9-migrate-ipd-lifecycle-plan-status-event-groups-and.backlog.md`, justified via `--scope-reason` in the begin receipt for finalize), plus the plan-record commit for `.aw/records/plans/pending/20261107-metastore-33-h58z9n-move-the-check-engine-hook-and-setter-git-content-readers-on.ipd.md` (in Scope-Paths).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `ffceq0`, `g5hpbb`, `tve77h`, `xexn45`, `snh19k` and `iqhzse` are executed. OQ-01 is resolved and not blocking.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code is not modified unless E-05 uncovers an unowned reader defect.

Safety: if prerequisite modules or `artifact_meta.read_at` reader implementations from `snh19k` or `iqhzse` are absent, stop and report immediately: that is an unsafe condition, not a scope question.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit h58z9n -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize h58z9n` itself.
